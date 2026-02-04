# Manual Installation Instructions

## Problem
The bundle modules don't auto-install from GitHub (investigating why). Use this manual workaround.

## Solution: Install Modules Manually

### Step 1: Install the orchestrator module
```bash
pip install -e git+https://github.com/michaeljabbour/amplifier-bundle-loop-safety@main#subdirectory=modules/orchestrator-loop-safe
```

### Step 2: Install the hook module
```bash
pip install -e git+https://github.com/michaeljabbour/amplifier-bundle-loop-safety@main#subdirectory=modules/hooks-loop-detector
```

### Step 3: Use the bundle
```bash
amplifier run --bundle git+https://github.com/michaeljabbour/amplifier-bundle-loop-safety@main "your prompt here"
```

## Verify Installation

Check that modules are installed:
```bash
pip list | grep loop
```

You should see:
```
amplifier-hooks-loop-detector       1.0.0
amplifier-orchestrator-loop-safe    1.0.0
```

## What This Gives You

- **Iteration limits**: Orchestrator stops after 100 iterations (warnings at 75 and 90)
- **Pattern detection**: Hook monitors for repetitive tool calls
- **Loop diagnostician**: Agent available to analyze stuck sessions

## Configuration

Default configuration in the bundle:
```yaml
# Orchestrator
max_iterations: 100
warn_at: [75, 90]

# Hook
detection_window: 10
similarity_threshold: 0.85
action_on_detect: warn
```

To customize, create your own bundle that includes this one and overrides the config.

## Uninstall

```bash
pip uninstall amplifier-orchestrator-loop-safe amplifier-hooks-loop-detector
```
