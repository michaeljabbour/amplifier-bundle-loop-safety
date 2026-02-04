"""Loop detector hook module for Amplifier."""

from .detector import LoopDetectorHook


async def mount(coordinator, config: dict):
    """
    Initialize and register loop detection hooks.

    Args:
        coordinator: Module coordinator for hook registration
        config: Hook configuration

    Returns:
        Cleanup function to unregister handlers
    """
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

    # Return cleanup function
    def cleanup():
        for unregister in handlers:
            unregister()

    return cleanup


__all__ = ["mount", "LoopDetectorHook"]
