#!/bin/bash

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Load environment variables
export $(cat .env | xargs)

# Check if TELEGRAM_BOT_TOKEN is set
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" == "your_bot_token_here" ]; then
    echo "WARNING: TELEGRAM_BOT_TOKEN is not set or is default. Bot service may fail."
    echo "Please update .env with your actual token."
fi

echo "Starting local environment..."
docker-compose -f docker-compose.local.yml up --build -d

echo "Services started:"
echo "- Admin Panel: http://localhost:3000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Database: localhost:5432"
echo "- Redis: localhost:6379"
echo ""
echo "To stop: docker-compose -f docker-compose.local.yml down"
