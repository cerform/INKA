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

# Set Python path
ENV PYTHONPATH=/app
ENV PORT=8080

# Run bot
CMD ["python", "apps/bot/src/main.py"]
