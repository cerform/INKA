FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot bot
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["python", "bot/main.py"]
