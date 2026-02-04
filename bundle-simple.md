---
bundle:
  name: loop-safety
  version: 1.0.0
  description: Loop safety bundle with iteration limits and pattern detection

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

# Direct module references (no behavior wrapper)
session:
  orchestrator:
    module: orchestrator-loop-safe
    source: git+https://github.com/michaeljabbour/amplifier-bundle-loop-safety@main#subdirectory=modules/orchestrator-loop-safe
    config:
      max_iterations: 100
      warn_at: [75, 90]

hooks:
  - module: hooks-loop-detector
    source: git+https://github.com/michaeljabbour/amplifier-bundle-loop-safety@main#subdirectory=modules/hooks-loop-detector
    config:
      detection_window: 10
      similarity_threshold: 0.85
      action_on_detect: warn

agents:
  include:
    - loop-safety:loop-diagnostician

context:
  include:
    - loop-safety:context/loop-safety-awareness.md
---

# Loop Safety Bundle

Provides configurable safety mechanisms to prevent runaway agent loops.

@loop-safety:context/loop-safety-awareness.md

---

@foundation:context/shared/common-system-base.md
