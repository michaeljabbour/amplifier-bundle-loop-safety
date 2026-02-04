# Loop Safety Guide

Complete guide to understanding and configuring loop safety mechanisms in Amplifier.

## Understanding the Problem

AI agents can get stuck in infinite loops when:

1. **Monitoring external processes** - Polling for completion without exit conditions
2. **Tool results ignored** - Making same call repeatedly without using results
3. **Context loss** - Compaction removes evidence of prior work
4. **Missing stop conditions** - No maximum iteration limits configured

### Real-World Example

From an actual incident (Session ID: 95bf4d89-7a84-4dcb-8364-46538f3bb79d):

```
Iterations: 452 bash calls over 1hr 40min
Pattern: tail -30 results/log.log (identical every time)
Compactions: 467 (agent lost awareness of looping)
Outcome: API errors finally stopped execution
```

## The Two Safety Mechanisms

### Mechanism 1: Hard Limits (orchestrator-loop-safe)

**What it does:**
- Counts iterations in the agent loop
- Warns at configurable thresholds
- Stops execution at maximum
- Requests graceful wrap-up

**When to use:**
- Want guaranteed stop condition
- Cost control is important
- Production environments

**Configuration:**
```yaml
session:
  orchestrator:
    module: orchestrator-loop-safe
    config:
      max_iterations: 100
      warn_at: [75, 90]
```

### Mechanism 2: Pattern Detection (hooks-loop-detector)

**What it does:**
- Monitors tool call sequences
- Detects repetitive patterns
- Warns or blocks based on configuration
- Maintains state across context compaction

**When to use:**
- Want intelligent monitoring
- Catch loops early (before hard limit)
- Development/analysis work

**Configuration:**
```yaml
hooks:
  - module: hooks-loop-detector
    config:
      detection_window: 10
      similarity_threshold: 0.85
      action_on_detect: warn
```

## Configuration Strategies

### Choose Your Profile

| Profile | max_iterations | detect_window | action | Use Case |
|---------|----------------|---------------|--------|----------|
| **Strict** | 50 | 5 | deny | Production, cost-sensitive |
| **Balanced** | 100 | 10 | warn | General use |
| **Lenient** | 500 | 15 | warn | Development, debugging |
| **Monitor** | (none) | 20 | log | Visibility only |

### Tuning Guidelines

**If getting false positives:**
1. Increase similarity_threshold (0.85 → 0.95)
2. Increase detection_window (10 → 15)
3. Change action from "deny" to "warn"

**If loops not caught:**
1. Decrease similarity_threshold (0.85 → 0.75)
2. Decrease detection_window (10 → 5)
3. Lower max_iterations
4. Change action from "warn" to "deny"

**If tasks legitimately need many iterations:**
1. Increase max_iterations
2. Keep warnings for awareness
3. Use "warn" mode (not "deny")

## Using the Diagnostic Agent

When loop warnings trigger:

```
"Delegate to loop-safety:loop-diagnostician to analyze this pattern"
```

The agent will:
- Read your session event log
- Identify the specific loop pattern
- Explain why it happened
- Recommend exact configuration values

## Advanced Patterns

### Different Limits for Different Agents

```yaml
agents:
  - id: quick-classifier
    bundle: foundation
    overrides:
      session:
        orchestrator:
          config:
            max_iterations: 10  # Short tasks only
  
  - id: deep-researcher
    bundle: foundation
    overrides:
      session:
        orchestrator:
          config:
            max_iterations: 500  # Complex research OK
```

### Progressive Enforcement

```yaml
# Start permissive, tighten on detection
hooks:
  - module: hooks-loop-detector
    config:
      detection_window: 10
      action_on_detect: warn  # First time: warn
      
# If warnings ignored, orchestrator stops it
session:
  orchestrator:
    config:
      max_iterations: 100  # Hard stop
```

## Monitoring and Observability

Both modules emit events for monitoring:

### Orchestrator Events
- `orchestrator:warning` - Warning threshold hit
- `orchestrator:limit_reached` - Max iterations reached
- `orchestrator:complete` - Execution finished (status field indicates why)

### Hook Events
- `loop-detector:pattern_detected` - Pattern matched threshold
- `loop-detector:action_taken` - Response action executed

### Logging

Enable debug logging to see loop safety in action:

```python
import logging
logging.getLogger("orchestrator_loop_safe").setLevel(logging.DEBUG)
logging.getLogger("hooks_loop_detector").setLevel(logging.DEBUG)
```

## FAQ

**Q: Will this slow down my sessions?**  
A: No measurable impact. Iteration counting is O(1), pattern detection is O(window_size).

**Q: Can I use just one mechanism?**  
A: Yes! Use orchestrator-only for hard limits, or hook-only for pattern detection.

**Q: Do these work with streaming?**  
A: The hook works with any orchestrator. The orchestrator doesn't support streaming yet.

**Q: What about recipe steps?**  
A: By default, loop detection only applies to root sessions. Recipe steps run independently with their own limits.

**Q: Can I disable loop safety temporarily?**  
A: Yes - use a different bundle without these modules, or set very high limits.

## Migration Guide

### From Unlimited Iterations

If currently using default orchestrator:

```yaml
# Before (unlimited)
session:
  orchestrator:
    module: loop-streaming

# After (safe limits)
session:
  orchestrator:
    module: orchestrator-loop-safe
    config:
      max_iterations: 100
```

### Adding to Existing Bundle

```yaml
# Your existing bundle
includes:
  - bundle: foundation
  # Add loop safety
  - bundle: loop-safety:behaviors/loop-safety
```

## Troubleshooting

**Session stopped unexpectedly at 100 iterations:**
- This is the default max_iterations
- Check logs for what the agent was doing
- Adjust limit if legitimately needed more iterations

**Too many false positive warnings:**
- Increase similarity_threshold
- Increase detection_window  
- Change action to "log" instead of "warn"

**Loop wasn't caught:**
- Decrease thresholds
- Use both mechanisms together
- Enable deny mode on hook

## Support

For issues or questions:
- Delegate to `loop-safety:loop-diagnostician` for analysis
- Check examples/ for configuration patterns
- Review session event logs for patterns
