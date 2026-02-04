"""Loop-safe orchestrator module for Amplifier."""

from .orchestrator import LoopSafeOrchestrator


async def mount(coordinator, config: dict):
    """
    Initialize and mount the loop-safe orchestrator.

    Args:
        coordinator: Module coordinator for registration
        config: Orchestrator configuration

    Returns:
        Orchestrator instance
    """
    orchestrator = LoopSafeOrchestrator(config=config)

    # Register with coordinator
    await coordinator.mount("session", orchestrator, name="orchestrator")

    # Register custom events for observability
    coordinator.register_contributor(
        "observability.events",
        "orchestrator-loop-safe",
        lambda: [
            "orchestrator:warning",
            "orchestrator:limit_reached",
        ],
    )

    return orchestrator


__all__ = ["mount", "LoopSafeOrchestrator"]
