"""Loop-safe orchestrator implementation."""

import logging
from typing import Any


logger = logging.getLogger(__name__)


class LoopSafeOrchestrator:
    """
    Orchestrator with configurable iteration limits to prevent runaway loops.

    This orchestrator implements a basic agent loop with safety guardrails:
    - Maximum iteration limit (default: 100, configurable)
    - Warning injection at thresholds (default: 75%, 90%)
    - Graceful wrap-up when limit reached
    - Full event emission for observability
    """

    def __init__(self, config: dict):
        """
        Initialize the loop-safe orchestrator.

        Args:
            config: Configuration dictionary with keys:
                - max_iterations (int): Maximum iterations before stopping (default: 100)
                - warn_at (list[int]): Iteration numbers to inject warnings (default: [75, 90])
                - default_provider (str): Provider name to use (default: first available)
                - stop_on_error (bool): Stop on tool errors (default: False)
        """
        self.max_iterations = config.get("max_iterations", 100)
        self.warn_at = config.get("warn_at", [75, 90])
        self.default_provider_name = config.get("default_provider")
        self.stop_on_error = config.get("stop_on_error", False)
        self.iteration_count = 0

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
    ) -> str:
        """
        Execute the agent loop with safety limits.

        Args:
            prompt: User input prompt
            context: Context manager for conversation state
            providers: Available LLM providers (keyed by name)
            tools: Available tools (keyed by name)
            hooks: Hook registry for lifecycle events

        Returns:
            Final response string
        """
        # Select provider
        provider_name = self.default_provider_name or next(iter(providers.keys()))
        provider = providers[provider_name]

        # Add user prompt to context
        await context.add_message({"role": "user", "content": prompt})

        # Reset iteration counter for this turn
        self.iteration_count = 0

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
                    context, provider, provider_name, hooks
                )

            # Get messages for LLM request
            messages = await context.get_messages_for_request()

            # Emit provider:request event
            await hooks.emit(
                "provider:request",
                {
                    "provider": provider_name,
                    "messages": messages,
                    "iteration": self.iteration_count,
                },
            )

            # Call LLM
            try:
                response = await provider.complete(messages)
            except Exception as e:
                logger.error(f"Provider error: {e}")
                await hooks.emit(
                    "provider:error",
                    {
                        "provider": provider_name,
                        "error": str(e),
                    },
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

            # Add assistant response to context
            await context.add_message(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": response.tool_calls if response.tool_calls else None,
                }
            )

            # If no tool calls, we're done
            if not response.tool_calls:
                await hooks.emit(
                    "orchestrator:complete",
                    {
                        "orchestrator": "orchestrator-loop-safe",
                        "turn_count": self.iteration_count,
                        "status": "success",
                    },
                )
                return response.content

            # Execute tool calls
            for tool_call in response.tool_calls:
                # Emit tool:pre event
                pre_result = await hooks.emit(
                    "tool:pre",
                    {
                        "tool_name": tool_call.name,
                        "tool_input": tool_call.input,
                        "tool_call_id": tool_call.id,
                    },
                )

                # Handle hook result
                if pre_result.action == "deny":
                    # Hook blocked the tool
                    tool_result_content = f"Tool blocked by hook: {pre_result.reason}"
                    logger.info(f"Tool {tool_call.name} denied by hook")

                elif pre_result.action == "inject_context":
                    # Hook wants to inject feedback
                    await context.add_message(
                        {
                            "role": pre_result.context_injection_role or "system",
                            "content": pre_result.context_injection,
                        }
                    )
                    # Continue with tool execution
                    tool_result_content = await self._execute_tool(
                        tool_call, tools, hooks
                    )

                else:
                    # Normal execution
                    tool_result_content = await self._execute_tool(
                        tool_call, tools, hooks
                    )

                # Add tool result to context
                await context.add_message(
                    {
                        "role": "tool",
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
                {
                    "tool_name": tool_call.name,
                    "error": error_msg,
                },
            )
            return f"Error: {error_msg}"

        try:
            result = await tool.execute(tool_call.input)

            # Emit tool:post event
            await hooks.emit(
                "tool:post",
                {
                    "tool_name": tool_call.name,
                    "tool_input": tool_call.input,
                    "tool_result": result,
                },
            )

            return result.output if hasattr(result, "output") else str(result)

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(f"Tool {tool_call.name} failed: {e}")

            await hooks.emit(
                "tool:error",
                {
                    "tool_name": tool_call.name,
                    "error": str(e),
                },
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

        await context.add_message(
            {
                "role": "system",
                "content": warning,
            }
        )

        logger.info(f"Injected iteration warning at {self.iteration_count}")

    async def _handle_limit_reached(
        self, context, provider, provider_name, hooks
    ) -> str:
        """Handle reaching max_iterations limit with graceful wrap-up."""
        # Inject termination message
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

        await context.add_message(
            {
                "role": "system",
                "content": termination_msg,
            }
        )

        # Get final wrap-up from LLM
        messages = await context.get_messages_for_request()

        await hooks.emit(
            "provider:request",
            {
                "provider": provider_name,
                "messages": messages,
                "iteration": self.iteration_count,
                "wrap_up": True,
            },
        )

        try:
            response = await provider.complete(messages)

            await hooks.emit(
                "provider:response",
                {
                    "provider": provider_name,
                    "response": response,
                },
            )

            # Add final response to context
            await context.add_message(
                {
                    "role": "assistant",
                    "content": response.content,
                }
            )

            # Emit completion with incomplete status
            await hooks.emit(
                "orchestrator:complete",
                {
                    "orchestrator": "orchestrator-loop-safe",
                    "turn_count": self.iteration_count,
                    "status": "incomplete",
                },
            )

            return response.content

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
