FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY libs/ ./libs/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY apps/bot/ ./apps/bot/

# Create packages structure for imports
RUN mkdir -p /app/packages && \
    touch /app/packages/__init__.py && \
    ln -s /app/libs/core/src /app/packages/core && \
    ln -s /app/libs/database/src /app/packages/db

# Set Python path
ENV PYTHONPATH=/app:/app/apps/bot
ENV PORT=8080

# Run bot
CMD ["python", "apps/bot/src/main.py"]
