# Loop Safety Configuration Examples

This directory contains example bundle configurations showing different loop safety profiles.

## Examples

### conservative.yaml
**Strict limits for production environments**

- Max iterations: 50
- Early warnings: 30, 40
- Pattern detection: deny on match
- Use when: Cost control critical, loops unexpected

### development.yaml
**Lenient limits for development work**

- Max iterations: 500
- Late warning: 400
- Pattern detection: warn only
- Use when: Complex debugging, want awareness not enforcement

### monitoring-only.yaml
**Pattern detection without hard limits**

- No iteration cap
- Pattern monitoring with logging
- Diagnostic agent included
- Use when: Want visibility, manual intervention preferred

## Usage

Copy the example that fits your needs and customize:

```bash
cp examples/conservative.yaml my-bundle.yaml
# Edit my-bundle.yaml to adjust thresholds
```

Or include and override:

```yaml
includes:
  - bundle: loop-safety:behaviors/loop-safety

# Override specific settings
session:
  orchestrator:
    config:
      max_iterations: 75  # Your custom limit
```

## Configuration Quick Reference

### Orchestrator Limits

```yaml
session:
  orchestrator:
    config:
      max_iterations: <N>    # How many iterations before stop
      warn_at: [X, Y]        # When to warn (iteration numbers)
```

### Pattern Detection

```yaml
hooks:
  - module: hooks-loop-detector
    config:
      detection_window: <N>      # Recent calls to analyze
      similarity_threshold: <X>  # 0.0-1.0, higher = stricter
      action_on_detect: <mode>   # warn | deny | log
```

## Tuning Guide

**If getting false positives** (warnings on legitimate work):
- Increase `similarity_threshold` (0.85 → 0.95)
- Increase `detection_window` (10 → 15)
- Change action to `log` instead of `warn`

**If loops not caught**:
- Decrease `similarity_threshold` (0.85 → 0.75)
- Decrease `detection_window` (10 → 5)
- Change action to `deny` instead of `warn`
- Lower `max_iterations` limit

**If need longer tasks**:
- Increase `max_iterations`
- Keep warnings for awareness
- Use `warn` mode to alert but not block
