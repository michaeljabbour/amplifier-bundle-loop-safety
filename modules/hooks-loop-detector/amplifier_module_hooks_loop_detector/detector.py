"""Loop detection hook implementation."""

import json
import logging
from collections import deque
from typing import Any

from amplifier_core.models import HookResult

logger = logging.getLogger(__name__)


class LoopDetectorHook:
    """
    Hook for detecting repetitive tool call patterns.

    Monitors tool execution for patterns that indicate infinite loops:
    - Same tool called repeatedly with identical arguments
    - Cyclic patterns (A→B→A→B...)
    - Long sequences without progress
    """

    def __init__(self, config: dict):
        """
        Initialize loop detector.

        Args:
            config: Configuration with keys:
                - detection_window (int): Recent calls to analyze (default: 10)
                - similarity_threshold (float): Pattern match threshold (default: 0.85)
                - action_on_detect (str): "warn" | "deny" | "log" (default: "warn")
                - apply_to_sub_sessions (bool): Monitor sub-sessions (default: False)
                - enabled_events (list[str]): Events to monitor (default: ["tool:post"])
        """
        self.detection_window = config.get("detection_window", 10)
        self.similarity_threshold = config.get("similarity_threshold", 0.85)
        self.action_on_detect = config.get("action_on_detect", "warn")
        self.apply_to_sub_sessions = config.get("apply_to_sub_sessions", False)

        # State: sliding window of recent tool call signatures
        self.recent_calls = deque(maxlen=self.detection_window)

        # Track if we've already warned (avoid spam)
        self.already_warned = False

        logger.info(
            f"LoopDetectorHook initialized: window={self.detection_window}, "
            f"threshold={self.similarity_threshold}, action={self.action_on_detect}"
        )

    async def __call__(self, event: str, data: dict[str, Any]) -> HookResult:
        """
        Handle lifecycle events.

        Args:
            event: Event name (e.g., "tool:post")
            data: Event-specific data

        Returns:
            HookResult indicating action to take
        """
        # Policy: Skip sub-sessions unless configured
        if not self.apply_to_sub_sessions and data.get("parent_id"):
            return HookResult(action="continue")

        # Monitor tool:post events
        if event == "tool:post":
            # Compute signature for this call
            signature = self._compute_signature(data)
            self.recent_calls.append(signature)

            # Check for loops
            is_loop, description = self._detect_loop()

            if is_loop and not self.already_warned:
                self.already_warned = True
                logger.warning(f"Loop detected: {description}")
                return self._handle_detection(description)

        return HookResult(action="continue")

    def _compute_signature(self, data: dict) -> str:
        """
        Create a signature for pattern matching.

        Args:
            data: tool:post event data

        Returns:
            Signature string: "tool_name:args_hash"
        """
        tool_name = data.get("tool_name", "unknown")
        tool_input = data.get("tool_input", {})

        # Normalize arguments for comparison
        try:
            args_normalized = json.dumps(tool_input, sort_keys=True)
            args_hash = hash(args_normalized)
        except (TypeError, ValueError):
            # Fallback if args aren't JSON-serializable
            args_hash = hash(str(tool_input))

        return f"{tool_name}:{args_hash}"

    def _calculate_similarity(self, sig1: str, sig2: str) -> float:
        """
        Calculate similarity between two tool signatures.

        Args:
            sig1: First signature
            sig2: Second signature

        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            name1, hash1 = sig1.split(":", 1)
            name2, hash2 = sig2.split(":", 1)
        except ValueError:
            return 0.0

        # Different tools = no similarity
        if name1 != name2:
            return 0.0

        # Same tool, exact same arguments = perfect match
        if hash1 == hash2:
            return 1.0

        # Same tool, different arguments = partial similarity
        return 0.5

    def _detect_loop(self) -> tuple[bool, str]:
        """
        Detect if recent calls show a repetitive pattern.

        Returns:
            (is_loop, description) tuple
        """
        if len(self.recent_calls) < 5:  # Minimum 5 calls for pattern
            return False, ""

        # Get recent calls for analysis
        recent = list(self.recent_calls)

        # Check for simple loop: all calls identical
        first_sig = recent[0]
        identical_count = sum(1 for sig in recent if sig == first_sig)

        if identical_count == len(recent):
            tool_name = first_sig.split(":", 1)[0]
            return (
                True,
                f"Same tool '{tool_name}' called {len(recent)} times with identical arguments",
            )

        # Check for high average similarity
        if len(recent) >= 5:
            # Calculate pairwise similarities for last 5
            last_five = recent[-5:]
            similarities = []

            for i in range(len(last_five) - 1):
                sim = self._calculate_similarity(last_five[i], last_five[i + 1])
                similarities.append(sim)

            avg_similarity = sum(similarities) / len(similarities)

            if avg_similarity >= self.similarity_threshold:
                tool_name = last_five[0].split(":", 1)[0]
                return (
                    True,
                    f"Repetitive pattern detected: tool '{tool_name}' similarity={avg_similarity:.2f}",
                )

        return False, ""

    def _handle_detection(self, description: str) -> HookResult:
        """
        Handle detected loop based on configuration.

        Args:
            description: Human-readable loop description

        Returns:
            HookResult with appropriate action
        """
        message = f"""<system-reminder source="hooks-loop-detector">
⚠️ **Repetitive Pattern Detected**

{description}

This may indicate an infinite loop. Consider:
- Is this task making measurable progress?
- Should you try a different approach?
- Can you delegate to an agent instead of polling?
- Should you return results to the user?

For analysis: delegate to loop-safety:loop-diagnostician
</system-reminder>"""

        if self.action_on_detect == "deny":
            return HookResult(
                action="deny",
                reason=f"Loop detected - blocking to prevent infinite execution: {description}",
            )

        elif self.action_on_detect == "warn":
            return HookResult(
                action="inject_context",
                context_injection=message,
                context_injection_role="system",
            )

        else:  # "log"
            # Just log, don't inject into agent context
            logger.warning(f"Loop detected (log-only mode): {description}")
            return HookResult(action="continue")
