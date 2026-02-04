# Loop Safety Capabilities

You have access to loop safety mechanisms that prevent runaway agent sessions.

## Protection Mechanisms

### 1. Iteration Limits
The orchestrator enforces a maximum iteration count (default: 100):
- Warns at configured thresholds (default: 75%, 90%)
- Gracefully terminates when limit reached
- Requests wrap-up summary before stopping

### 2. Pattern Detection
A hook monitors for repetitive tool call patterns:
- Tracks recent tool calls in a sliding window
- Detects identical or highly similar sequences
- Warns or blocks based on configuration

## When Loop Detection Triggers

If you see warnings about repetitive patterns:

1. **Assess progress** - Are you making measurable progress?
2. **Consider alternatives** - Is there a different approach?
3. **Delegate if stuck** - Can an agent handle this better?
4. **Return to user** - Should you report findings and stop?

## Diagnostic Agent

**loop-safety:loop-diagnostician** - Expert for analyzing stuck sessions

Delegate to this agent when:
- Loop warnings trigger
- Session hits iteration limits
- You notice repetitive patterns
- Need help tuning detection thresholds

## Configuration

Loop safety is configured in your bundle:

```yaml
session:
  orchestrator:
    config:
      max_iterations: 100  # Adjust based on task complexity
      warn_at: [75, 90]    # When to warn

hooks:
  - module: hooks-loop-detector
    config:
      detection_window: 10
      action_on_detect: warn  # warn | deny | log
```

For detailed documentation: @loop-safety:docs/LOOP_SAFETY_GUIDE.md
