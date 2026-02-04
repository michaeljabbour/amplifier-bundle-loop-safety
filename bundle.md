---
bundle:
  name: loop-safety
  version: 1.0.0
  description: Prevents runaway agent loops via iteration limits and pattern detection

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: loop-safety:behaviors/loop-safety
---

# Loop Safety Bundle

Provides configurable safety mechanisms to prevent runaway agent loops through:

- **Iteration limits** - Hard caps on orchestrator loop iterations
- **Pattern detection** - Intelligent monitoring for repetitive tool calls  
- **Diagnostic capabilities** - Expert agent for analyzing stuck sessions

@loop-safety:context/loop-safety-awareness.md

---

@foundation:context/shared/common-system-base.md
