---
bundle:
  name: loop-safety
  version: 1.0.0
  description: Prevents runaway agent loops via iteration limits and pattern detection

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main

# Override orchestrator with loop-safe version
# Note: Modules must be installed via pip (see MANUAL_INSTALL.md)
session:
  orchestrator:
    module: orchestrator-loop-safe
    # For local development, use file:// source:
    # source: file:///path/to/amplifier-bundle-loop-safety/modules/orchestrator-loop-safe
    # For GitHub, use git+ source after pushing:
    # source: git+https://github.com/YOUR_USER/amplifier-bundle-loop-safety@main#subdirectory=modules/orchestrator-loop-safe
    config:
      max_iterations: 100
      warn_at: [75, 90]

# Pattern detection hook
hooks:
  - module: hooks-loop-detector
    # For local development, use file:// source:
    # source: file:///path/to/amplifier-bundle-loop-safety/modules/hooks-loop-detector
    config:
      detection_window: 10
      similarity_threshold: 0.85
      action_on_detect: warn
      apply_to_sub_sessions: false

# Diagnostic agent
agents:
  include:
    - loop-safety:loop-diagnostician

# Awareness context
context:
  include:
    - loop-safety:context/loop-safety-awareness.md
---

# Loop Safety Bundle

Provides configurable safety mechanisms to prevent runaway agent loops through:

- **Iteration limits** - Hard caps on orchestrator loop iterations
- **Pattern detection** - Intelligent monitoring for repetitive tool calls
- **Diagnostic capabilities** - Expert agent for analyzing stuck sessions

## Installation

The custom modules require manual installation:

```bash
# Clone the bundle
git clone https://github.com/YOUR_USER/amplifier-bundle-loop-safety
cd amplifier-bundle-loop-safety

# Install modules
pip install -e modules/orchestrator-loop-safe/
pip install -e modules/hooks-loop-detector/

# Add and use the bundle
amplifier bundle add git+https://github.com/YOUR_USER/amplifier-bundle-loop-safety@main
amplifier bundle use loop-safety
```

## Configuration

The orchestrator and hooks can be configured in the bundle:

```yaml
session:
  orchestrator:
    module: orchestrator-loop-safe
    config:
      max_iterations: 100    # Maximum iterations before stopping
      warn_at: [75, 90]      # Iteration numbers to inject warnings

hooks:
  - module: hooks-loop-detector
    config:
      detection_window: 10           # Number of recent calls to analyze
      similarity_threshold: 0.85     # 0-1, higher = stricter detection
      action_on_detect: warn         # warn, inject_context, or deny
```

@loop-safety:context/loop-safety-awareness.md

---

@foundation:context/shared/common-system-base.md
