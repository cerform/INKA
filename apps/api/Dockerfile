# Build Stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY libs/ ./libs/

# Install dependencies - we use -e for libs initially to ensure they are found, 
# then build a wheel or just copy the installed site-packages.
# Using .[dev] is avoided here, only core dependencies.
RUN pip install --no-cache-dir .

# Runtime Stage
FROM python:3.12-slim AS runtime

# Create a non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser

WORKDIR /app

# Copy site-packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application and libs
COPY apps/api/ ./apps/api/
COPY libs/ ./libs/

# Re-create package structure (consistent with app imports)
RUN mkdir -p /app/packages && \
    touch /app/packages/__init__.py && \
    ln -s /app/libs/core/src /app/packages/core && \
    ln -s /app/libs/database/src /app/packages/db && \
    ln -s /app/libs/orchestrator/src /app/packages/orchestrator && \
    ln -s /app/libs/chaos /app/packages/chaos && \
    ln -s /app/libs/quality/src /app/packages/quality && \
    ln -s /app/libs/observability/src /app/packages/observability 2>/dev/null || true


# Set ownership to non-root user
RUN chown -R appuser:appgroup /app

# Set environments
ENV PYTHONPATH=/app/apps/api/src:/app/packages
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8080

# Cloud Run healthcheck (using the endpoint we verified exists)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

