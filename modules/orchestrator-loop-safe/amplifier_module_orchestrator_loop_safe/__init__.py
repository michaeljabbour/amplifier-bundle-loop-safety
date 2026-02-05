"""Loop-safe orchestrator module for Amplifier."""

# Amplifier module metadata
__amplifier_module_type__ = "orchestrator"

import logging
from typing import Any

from .orchestrator import LoopSafeOrchestrator

logger = logging.getLogger(__name__)


async def mount(coordinator, config: dict[str, Any] | None = None):
    """Mount the loop-safe orchestrator module."""
    config = config or {}

    orchestrator = LoopSafeOrchestrator(config=config)

    # Register with coordinator
    await coordinator.mount("orchestrator", orchestrator)

    # Register custom events for observability
    coordinator.register_contributor(
        "observability.events",
        "orchestrator-loop-safe",
        lambda: [
            "orchestrator:warning",
            "orchestrator:limit_reached",
        ],
    )

    logger.info(
        f"Mounted LoopSafeOrchestrator: max_iterations={config.get('max_iterations', 100)}"
    )
    return


__all__ = ["mount", "LoopSafeOrchestrator"]
