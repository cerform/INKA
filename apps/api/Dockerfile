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
COPY apps/api/ ./apps/api/

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "alembic -c libs/database/alembic.ini upgrade head && uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000"]
