"""Loop-safe orchestrator implementation."""

import logging
from typing import Any

from amplifier_core.message_models import ChatRequest, Message, ToolSpec

logger = logging.getLogger(__name__)


def _content_to_string(content) -> str:
    """Convert content (string or list of blocks) to string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if hasattr(block, 'text'):
                text_parts.append(block.text)
            elif isinstance(block, dict) and 'text' in block:
                text_parts.append(block['text'])
        return ''.join(text_parts)
    return str(content)


def _serialize_content(content) -> str | list[dict]:
    """Serialize content blocks to dicts for storage."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return [
            block.model_dump() if hasattr(block, "model_dump") else block
            for block in content
        ]
    return str(content)


class LoopSafeOrchestrator:
    """
    Orchestrator with configurable iteration limits to prevent runaway loops.
    """

    def __init__(self, config: dict):
        self.max_iterations = config.get("max_iterations", 100)
        self.warn_at = config.get("warn_at", [75, 90])
        self.default_provider_name = config.get("default_provider")
        self.stop_on_error = config.get("stop_on_error", False)
        self.iteration_count = 0
        self.coordinator = None

        logger.info(
            f"LoopSafeOrchestrator initialized: max_iterations={self.max_iterations}, "
            f"warn_at={self.warn_at}"
        )

    async def execute(
        self,
        prompt: str,
        context,
        providers: dict[str, Any],
        tools: dict[str, Any],
        hooks,
        coordinator=None,
    ) -> str:
        """Execute the agent loop with safety limits."""
        self.coordinator = coordinator

        # Select provider
        provider_name = self.default_provider_name or next(iter(providers.keys()))
        provider = providers[provider_name]

        # Add user prompt to context
        await context.add_message({"role": "user", "content": prompt})

        # Reset iteration counter
        self.iteration_count = 0

        # Build tools list for ChatRequest
        tools_list = None
        if tools:
            tools_list = [
                ToolSpec(
                    name=t.name,
                    description=t.description,
                    parameters=t.input_schema,
                )
                for t in tools.values()
            ]

        # Main loop
        while True:
            self.iteration_count += 1

            # Check iteration warnings
            if self.iteration_count in self.warn_at:
                await self._inject_warning(context)

            # Check iteration limit
            if self.iteration_count >= self.max_iterations:
                logger.warning(f"Reached max_iterations limit: {self.max_iterations}")
                await hooks.emit(
                    "orchestrator:limit_reached",
                    {
                        "iteration": self.iteration_count,
                        "max_iterations": self.max_iterations,
                    },
                )
                return await self._handle_limit_reached(
                    context, provider, provider_name, hooks, tools_list
                )

            # Get messages for LLM request
            message_dicts = await context.get_messages_for_request(provider=provider)
            messages = [Message(**msg) for msg in message_dicts]
            chat_request = ChatRequest(messages=messages, tools=tools_list)

            # Emit provider:request event
            await hooks.emit(
                "provider:request",
                {
                    "provider": provider_name,
                    "messages": message_dicts,
                    "iteration": self.iteration_count,
                },
            )

            # Call LLM
            try:
                response = await provider.complete(chat_request)
            except Exception as e:
                logger.error(f"Provider error: {e}")
                await hooks.emit(
                    "provider:error",
                    {"provider": provider_name, "error": str(e)},
                )
                raise

            # Emit provider:response event
            await hooks.emit(
                "provider:response",
                {
                    "provider": provider_name,
                    "response": response,
                    "usage": getattr(response, "usage", None),
                },
            )

            # Extract content and tool calls using provider's parse method
            raw_content = getattr(response, "content", None) or ""
            response_text = _content_to_string(raw_content)

            # Use provider's parse_tool_calls method
            tool_calls = provider.parse_tool_calls(response)

            # Build assistant message
            if tool_calls:
                # Serialize tool_calls properly (key is "tool", not "name")
                assistant_msg = {
                    "role": "assistant",
                    "content": _serialize_content(raw_content),
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "tool": tc.name,
                            "arguments": tc.arguments,
                        }
                        for tc in tool_calls
                    ],
                }
            else:
                assistant_msg = {
                    "role": "assistant",
                    "content": _serialize_content(raw_content),
                }

            await context.add_message(assistant_msg)

            # If no tool calls, we're done
            if not tool_calls:
                await hooks.emit(
                    "orchestrator:complete",
                    {
                        "orchestrator": "orchestrator-loop-safe",
                        "turn_count": self.iteration_count,
                        "status": "success",
                    },
                )
                return response_text

            # Execute tool calls
            for tool_call in tool_calls:
                # Emit tool:pre event
                pre_result = await hooks.emit(
                    "tool:pre",
                    {
                        "tool_name": tool_call.name,
                        "tool_input": tool_call.arguments,
                        "tool_call_id": tool_call.id,
                    },
                )

                # Handle hook result
                if pre_result and pre_result.action == "deny":
                    tool_result_content = f"Tool blocked by hook: {pre_result.reason}"
                    logger.info(f"Tool {tool_call.name} denied by hook")
                elif pre_result and pre_result.action == "inject_context":
                    await context.add_message(
                        {
                            "role": getattr(pre_result, "context_injection_role", "system") or "system",
                            "content": pre_result.context_injection,
                        }
                    )
                    tool_result_content = await self._execute_tool(tool_call, tools, hooks)
                else:
                    tool_result_content = await self._execute_tool(tool_call, tools, hooks)

                # Add tool result to context (MUST include name field)
                await context.add_message(
                    {
                        "role": "tool",
                        "name": tool_call.name,  # Required!
                        "tool_call_id": tool_call.id,
                        "content": tool_result_content,
                    }
                )

        # Should never reach here
        await hooks.emit(
            "orchestrator:complete",
            {
                "orchestrator": "orchestrator-loop-safe",
                "turn_count": self.iteration_count,
                "status": "incomplete",
            },
        )
        return ""

    async def _execute_tool(self, tool_call, tools: dict, hooks) -> str:
        """Execute a tool and handle errors."""
        tool = tools.get(tool_call.name)

        if not tool:
            error_msg = f"Tool '{tool_call.name}' not found"
            logger.error(error_msg)
            await hooks.emit(
                "tool:error",
                {"tool_name": tool_call.name, "error": error_msg},
            )
            return f"Error: {error_msg}"

        try:
            result = await tool.execute(tool_call.arguments)

            # Emit tool:post event
            await hooks.emit(
                "tool:post",
                {
                    "tool_name": tool_call.name,
                    "tool_input": tool_call.arguments,
                    "tool_result": result,
                },
            )

            # Ensure result is always a string
            if hasattr(result, "output"):
                output = result.output
                if isinstance(output, dict):
                    # Format dict output as string (e.g., bash tool results)
                    parts = []
                    if output.get("stdout"):
                        parts.append(output["stdout"])
                    if output.get("stderr"):
                        parts.append(f"stderr: {output['stderr']}")
                    return "\n".join(parts) if parts else "(empty output)"
                return str(output) if output else "(empty output)"
            return str(result) if result else "(empty output)"

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(f"Tool {tool_call.name} failed: {e}")
            await hooks.emit(
                "tool:error",
                {"tool_name": tool_call.name, "error": str(e)},
            )
            if self.stop_on_error:
                raise
            return error_msg

    async def _inject_warning(self, context):
        """Inject warning at iteration threshold."""
        percentage = int((self.iteration_count / self.max_iterations) * 100)
        warning = f"""<system-reminder source="orchestrator-loop-safe">
⚠️ **Iteration Warning**
You are at iteration {self.iteration_count} of {self.max_iterations} maximum ({percentage}%).

Consider:
- Have you made progress toward the goal?
- Are you stuck in a monitoring or polling loop?
- Should you summarize progress and return to the user?
</system-reminder>"""

        await context.add_message({"role": "system", "content": warning})
        logger.info(f"Injected iteration warning at {self.iteration_count}")

    async def _handle_limit_reached(
        self, context, provider, provider_name, hooks, tools_list
    ) -> str:
        """Handle reaching max_iterations limit with graceful wrap-up."""
        termination_msg = f"""<system-reminder source="orchestrator-loop-safe">
🛑 **Maximum Iterations Reached**
Stopped at {self.max_iterations} iterations to prevent runaway execution.

You MUST now:
1. Summarize the progress made
2. Explain what was accomplished
3. Indicate what remains to be done
4. Return control to the user

Do NOT attempt to continue the task. Provide a summary and stop.
</system-reminder>"""

        await context.add_message({"role": "system", "content": termination_msg})

        # Get final wrap-up from LLM (no tools - force text response)
        message_dicts = await context.get_messages_for_request(provider=provider)
        messages = [Message(**msg) for msg in message_dicts]
        chat_request = ChatRequest(messages=messages, tools=None)

        await hooks.emit(
            "provider:request",
            {
                "provider": provider_name,
                "messages": message_dicts,
                "iteration": self.iteration_count,
                "wrap_up": True,
            },
        )

        try:
            response = await provider.complete(chat_request)
            await hooks.emit(
                "provider:response",
                {"provider": provider_name, "response": response},
            )

            raw_content = getattr(response, "content", None) or ""
            await context.add_message(
                {"role": "assistant", "content": _serialize_content(raw_content)}
            )

            await hooks.emit(
                "orchestrator:complete",
                {
                    "orchestrator": "orchestrator-loop-safe",
                    "turn_count": self.iteration_count,
                    "status": "incomplete",
                },
            )

            return _content_to_string(raw_content)

        except Exception as e:
            logger.error(f"Wrap-up LLM call failed: {e}")
            await hooks.emit(
                "orchestrator:complete",
                {
                    "orchestrator": "orchestrator-loop-safe",
                    "turn_count": self.iteration_count,
                    "status": "error",
                },
            )
            return f"Reached iteration limit. Failed to generate summary: {str(e)}"
