FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY libs/ ./libs/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY apps/api/ ./apps/api/

# Create packages structure for imports
RUN mkdir -p /app/packages && \
    touch /app/packages/__init__.py && \
    ln -s /app/libs/core/src /app/packages/core && \
    ln -s /app/libs/database/src /app/packages/db

# Bridge inconsistent import paths (apps.api.app -> apps.api.src.app)
RUN ln -s /app/apps/api/src/app /app/apps/api/app && \
    ln -s /app/apps/api/src/deps /app/apps/api/deps 2>/dev/null || true && \
    ln -s /app/apps/api/src/v1 /app/apps/api/v1 2>/dev/null || true

# Expose port
EXPOSE 8080

# Environment variables
ENV PYTHONPATH=/app:/app/apps/api
ENV PORT=8080

# Run server (migrations should be run separately via Cloud Run Jobs or a migration step)
CMD ["uvicorn", "apps.api.src.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
