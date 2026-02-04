# hooks-loop-detector

Hook module for detecting repetitive tool call patterns that indicate infinite loops.

## Features

- **Sliding window analysis** (default: last 10 calls)
- **Similarity-based detection** (configurable threshold)
- **Multiple response modes** (warn, deny, log)
- **Policy behavior** (root-only by default)
- **Maintains own state** (survives context compaction)

## Configuration

```yaml
hooks:
  - module: hooks-loop-detector
    source: git+https://github.com/org/amplifier-bundle-loop-safety@main#subdirectory=modules/hooks-loop-detector
    config:
      detection_window: 10          # Recent calls to analyze
      similarity_threshold: 0.85    # Pattern match threshold (0.0-1.0)
      action_on_detect: warn        # warn | deny | log
      apply_to_sub_sessions: false  # Monitor sub-sessions
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `detection_window` | int | 10 | Number of recent calls to analyze |
| `similarity_threshold` | float | 0.85 | Pattern match threshold (0.0-1.0) |
| `action_on_detect` | str | "warn" | Response mode: "warn", "deny", or "log" |
| `apply_to_sub_sessions` | bool | false | Apply to sub-sessions (policy behavior) |
| `enabled_events` | list[str] | ["tool:post"] | Events to monitor |

## Detection Algorithm

### Pattern Types Detected

1. **Simple loops**: Same tool with identical arguments repeated N times
2. **High similarity sequences**: Tool calls with very similar arguments
3. **Threshold-based**: Configurable sensitivity via similarity_threshold

### Similarity Scoring

- **Identical tool + args**: 1.0 (perfect match)
- **Same tool, different args**: 0.5 (partial match)
- **Different tools**: 0.0 (no match)

### Response Modes

**warn** (default):
- Injects system message to agent
- Agent sees the warning and can self-correct
- Execution continues

**deny**:
- Blocks the tool call
- Returns error to agent
- Forces agent to try different approach

**log**:
- Logs warning to system
- No agent notification
- Execution continues normally

## Events Emitted

| Event | When | Data |
|-------|------|------|
| `loop-detector:pattern_detected` | Pattern matches threshold | description, similarity |
| `loop-detector:action_taken` | Response action executed | action, tool_name |

## Policy Behavior

By default, this hook applies only to **root sessions** (not sub-agents or recipe steps).

Set `apply_to_sub_sessions: true` to monitor all sessions.

## Installation

```bash
cd modules/hooks-loop-detector
pip install -e .
```

## Testing

```bash
pytest tests/
```

## License

MIT
