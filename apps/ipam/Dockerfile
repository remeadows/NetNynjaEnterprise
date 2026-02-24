# GridWatch IPAM Service - Multi-stage Dockerfile
# Build context: repo root (for access to services/shared-python)
# Build: docker build -f apps/ipam/Dockerfile --target production -t gridwatch-ipam .

# ==================================================
# Base image with Python 3.13 (Alpine - CDN accessible)
# ==================================================
FROM python:3.13.1-alpine AS base

# Security: Update system packages
RUN apk upgrade --no-cache

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apk add --no-cache \
    # Network tools for scanning
    iputils \
    nmap \
    nmap-scripts \
    arp-scan \
    net-tools \
    # Build dependencies
    build-base \
    postgresql-dev \
    musl-dev \
    # Runtime dependencies
    libpcap-dev

WORKDIR /app

# Install shared-python library (used by IPAM for DB pool, logging, health checks)
COPY services/shared-python/pyproject.toml /app/shared-python/pyproject.toml
COPY services/shared-python/src/ /app/shared-python/src/
RUN pip install --upgrade pip && \
    pip install /app/shared-python

# ==================================================
# Development stage
# ==================================================
FROM base AS development

# Install development dependencies
RUN pip install hatch

# Copy project files
COPY apps/ipam/pyproject.toml apps/ipam/README.md ./
COPY apps/ipam/src/ ./src/
RUN pip install -e ".[dev]"

# Default command for development
CMD ["python", "-m", "uvicorn", "ipam.main:app", "--host", "0.0.0.0", "--port", "3003", "--reload"]

# ==================================================
# Scanner stage (for network discovery)
# ==================================================
FROM base AS scanner

# Scanner needs elevated privileges for raw sockets
# Note: Container should be run with --cap-add=NET_RAW

COPY apps/ipam/pyproject.toml apps/ipam/README.md ./
COPY apps/ipam/src/ ./src/
RUN pip install .

# Scanner worker command
CMD ["python", "-m", "ipam.collectors.nats_handler"]

# ==================================================
# Production build stage
# ==================================================
FROM base AS builder

RUN pip install build

COPY apps/ipam/pyproject.toml apps/ipam/README.md ./
COPY apps/ipam/src/ ./src/

RUN pip wheel --no-deps --wheel-dir /app/wheels .

# ==================================================
# Production stage
# ==================================================
FROM python:3.13.1-alpine AS production

# Non-root user for security
RUN addgroup -g 1000 ipam && \
    adduser -u 1000 -G ipam -s /bin/sh -D ipam

# Install minimal runtime dependencies
RUN apk add --no-cache \
    iputils \
    libpq \
    libpcap

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Install shared-python (needed at runtime)
COPY --from=base /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Copy wheels and install
COPY --from=builder /app/wheels /app/wheels
RUN pip install --no-cache-dir /app/wheels/*.whl && rm -rf /app/wheels

# Copy source for reference (optional, can be removed for smaller image)
COPY --chown=ipam:ipam apps/ipam/src/ ./src/

USER ipam

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:3003/healthz').raise_for_status()"

EXPOSE 3003

CMD ["python", "-m", "uvicorn", "ipam.main:app", "--host", "0.0.0.0", "--port", "3003"]
