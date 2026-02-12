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

# Expose port
EXPOSE 8080

# Environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Run migrations and start server
CMD ["sh", "-c", "alembic -c libs/database/alembic.ini upgrade head && uvicorn apps.api.src.app.main:app --host 0.0.0.0 --port ${PORT}"]
