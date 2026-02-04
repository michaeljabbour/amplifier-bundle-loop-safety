# Amplifier Loop Safety Bundle

Prevents runaway agent loops through configurable iteration limits and intelligent pattern detection.

## The Problem

Amplifier sessions can get stuck in infinite loops when:
- Monitoring long-running processes by polling
- Repeating the same tool calls without progress
- Context compaction removes evidence of looping
- No hard stop limits exist

**Real example**: A session made 452 identical `tail` calls over 1hr 40min, hit 467 context compactions, and only stopped when API errors occurred.

## The Solution

This bundle provides **two independent safety mechanisms**:

### 1. orchestrator-loop-safe
Orchestrator with hard iteration limits:
- Default max: 100 iterations
- Warns at 75%, 90%
- Graceful wrap-up when limit reached
- Drop-in replacement for standard orchestrators

### 2. hooks-loop-detector  
Hook that detects repetitive patterns:
- Monitors last N tool calls
- Detects identical or similar sequences
- Configurable response (warn/deny/log)
- Root-session-only by default

## Quick Start

### Option A: Use the Behavior (Recommended)

Include the pre-packaged behavior in your bundle:

```yaml
includes:
  - bundle: git+https://github.com/org/amplifier-bundle-loop-safety@main
```

This gives you both modules with sensible defaults.

### Option B: Compose Modules Directly

For custom configuration:

```yaml
session:
  orchestrator:
    module: orchestrator-loop-safe
    source: git+https://github.com/org/amplifier-bundle-loop-safety@main#subdirectory=modules/orchestrator-loop-safe
    config:
      max_iterations: 150  # Custom limit
      warn_at: [100, 125]

hooks:
  - module: hooks-loop-detector
    source: git+https://github.com/org/amplifier-bundle-loop-safety@main#subdirectory=modules/hooks-loop-detector
    config:
      detection_window: 5
      action_on_detect: deny  # More aggressive
```

## Configuration Profiles

### Conservative (Production)
```yaml
includes:
  - bundle: loop-safety:behaviors/loop-safety

# Override in your bundle
session:
  orchestrator:
    config:
      max_iterations: 50
      warn_at: [30, 40]

hooks:
  - config:
      action_on_detect: deny
```

### Development (Lenient)
```yaml
includes:
  - bundle: loop-safety:behaviors/loop-safety

session:
  orchestrator:
    config:
      max_iterations: 500
      warn_at: [400]

hooks:
  - config:
      action_on_detect: warn  # Just warn, don't block
```

### Monitoring Only (Hook Only)
```yaml
# Just pattern detection, no hard limits
hooks:
  - module: hooks-loop-detector
    source: git+https://github.com/org/amplifier-bundle-loop-safety@main#subdirectory=modules/hooks-loop-detector
    config:
      detection_window: 20
      action_on_detect: log
```

## Components

| Component | Type | Purpose |
|-----------|------|---------|
| **orchestrator-loop-safe** | Orchestrator | Hard iteration limits |
| **hooks-loop-detector** | Hook | Pattern detection |
| **loop-diagnostician** | Agent | Stuck session analysis |
| **loop-safety behavior** | Behavior | Packaged configuration |

## Diagnostic Agent

When loop warnings trigger or sessions get stuck:

```
"Delegate to loop-safety:loop-diagnostician to analyze this pattern"
```

The agent will:
- Analyze recent tool call patterns
- Identify the root cause
- Recommend specific configuration adjustments
- Suggest fixes to resume progress

## Configuration Reference

### orchestrator-loop-safe

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_iterations` | int | 100 | Maximum iterations before stopping |
| `warn_at` | list[int] | [75, 90] | Iteration numbers for warnings |
| `default_provider` | str | (first) | Provider to use |
| `stop_on_error` | bool | false | Stop on tool errors |

### hooks-loop-detector

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `detection_window` | int | 10 | Recent calls to analyze |
| `similarity_threshold` | float | 0.85 | Pattern match threshold (0.0-1.0) |
| `action_on_detect` | str | "warn" | "warn" / "deny" / "log" |
| `apply_to_sub_sessions` | bool | false | Monitor sub-sessions |

## How It Works

### Orchestrator Safety
```
Iteration 1-74:  Normal execution
Iteration 75:    ⚠️ Warning injected to agent
Iteration 90:    ⚠️ Second warning
Iteration 100:   🛑 Limit reached, wrap-up requested
```

### Pattern Detection
```
Tool calls: [bash, bash, bash, bash, bash]
            └─ All identical ─────────────┘
               ↓
         Pattern detected (5 consecutive)
               ↓
         Warning injected to agent
```

### Combined Protection
Both mechanisms work independently:
- Orchestrator provides **guardrail** (can't exceed N iterations)
- Hook provides **intelligence** (warns at pattern detection, even if <N)

## Events Emitted

| Event | Source | When |
|-------|--------|------|
| `orchestrator:warning` | orchestrator-loop-safe | Warning threshold hit |
| `orchestrator:limit_reached` | orchestrator-loop-safe | Max iterations hit |
| `orchestrator:complete` | orchestrator-loop-safe | Execution ends |
| `loop-detector:pattern_detected` | hooks-loop-detector | Pattern matches |
| `loop-detector:action_taken` | hooks-loop-detector | Response executed |

## Module Installation

For standalone use:

```bash
# Orchestrator
cd modules/orchestrator-loop-safe
pip install -e .

# Hook
cd modules/hooks-loop-detector
pip install -e .
```

## Examples

See `examples/` directory for complete bundle configurations:
- `conservative.yaml` - Strict limits for production
- `development.yaml` - Lenient limits for debugging
- `monitoring.yaml` - Hook-only pattern detection

## Testing

Each module includes tests:

```bash
cd modules/orchestrator-loop-safe && pytest tests/
cd modules/hooks-loop-detector && pytest tests/
```

## Philosophy

This bundle follows Amplifier's **"mechanism, not policy"** philosophy:

- **Kernel provides**: Hook system, event emission, module contracts
- **Modules provide**: Safety policies (iteration limits, pattern detection)
- **Users decide**: Which safety level matches their needs

Different teams need different loop limits:
- Research: May want unlimited iterations
- Production: Strict limits (50)
- Development: Permissive limits (500)
- Monitoring: Long-running polls (1000+)

This bundle provides the safety mechanisms; users choose their policy through configuration.

## Contributing

See `docs/DEVELOPMENT.md` for contribution guidelines.

## License

MIT
