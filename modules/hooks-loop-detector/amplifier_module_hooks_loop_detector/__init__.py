"""Loop detector hook module for Amplifier."""

# Amplifier module metadata
__amplifier_module_type__ = "hook"

import logging
from typing import Any

from .detector import LoopDetectorHook

logger = logging.getLogger(__name__)


async def mount(coordinator, config: dict[str, Any] | None = None):
    """
    Initialize and register loop detection hooks.

    Args:
        coordinator: Module coordinator for hook registration
        config: Hook configuration
    """
    config = config or {}

    # Create hook instance
    hook = LoopDetectorHook(config=config)

    # Register for events
    enabled_events = config.get("enabled_events", ["tool:post"])
    handlers = []

    for event in enabled_events:
        unregister = coordinator.hooks.register(
            event=event,
            handler=hook,
            priority=10,  # Run early
            name=f"loop-detector-{event}",
        )
        handlers.append(unregister)

    # Register custom events for observability
    coordinator.register_contributor(
        "observability.events",
        "hooks-loop-detector",
        lambda: [
            "loop-detector:pattern_detected",
            "loop-detector:action_taken",
        ],
    )

    logger.info(
        f"Mounted LoopDetectorHook: events={enabled_events}, "
        f"threshold={config.get('similarity_threshold', 0.85)}"
    )
    return


__all__ = ["mount", "LoopDetectorHook"]
