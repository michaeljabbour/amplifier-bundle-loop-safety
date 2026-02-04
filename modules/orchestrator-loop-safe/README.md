# orchestrator-loop-safe

Orchestrator module with configurable iteration limits to prevent runaway loops.

## Features

- **Hard iteration limit** (default: 100, configurable)
- **Progressive warnings** at thresholds (default: 75%, 90%)
- **Graceful wrap-up** when limit reached
- **Full observability** via event emission
- **Drop-in replacement** for standard orchestrators

## Installation

```bash
pip install -e .
```

## Configuration

```yaml
session:
  orchestrator:
    module: orchestrator-loop-safe
    config:
      max_iterations: 100
      warn_at: [75, 90]
```

## License

MIT
