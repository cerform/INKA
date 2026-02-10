FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY libs/ ./libs/

# Install Python dependencies
RUN pip install --no-cache-dir -e .[dev]

# Copy application code
COPY apps/bot/ ./apps/bot/

# Run bot
CMD ["python", "-m", "apps.bot.src.main"]
