---
bundle:
  name: loop-safety-direct
  version: 1.0.0
  description: Loop safety - direct module test (bypass behavior wrapper)

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

# Reference modules with #subdirectory syntax directly
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
      apply_to_sub_sessions: false

agents:
  include:
    - loop-safety:loop-diagnostician

context:
  include:
    - loop-safety:context/loop-safety-awareness.md
---

# Loop Safety Bundle - Direct Test

Testing modules referenced directly from bundle.md (no behavior wrapper).

@loop-safety:context/loop-safety-awareness.md

---

@foundation:context/shared/common-system-base.md
