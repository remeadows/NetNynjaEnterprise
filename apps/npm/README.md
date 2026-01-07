# NetNynja NPM Service

Network Performance Monitoring service for NetNynja Enterprise.

## Features

- SNMP polling for device and interface metrics
- Real-time alerting with configurable thresholds
- VictoriaMetrics integration for time-series storage
- Multi-vendor device support

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run service
uvicorn npm.main:app --reload --port 3004
```

## API

Service runs on port 3004. See OpenAPI docs at `/docs`.
