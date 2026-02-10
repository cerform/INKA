# INKA - Tattoo Salon Admin System

Production-ready monorepo for INKA tattoo salon administration system with Telegram bot, REST API, and admin panel.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ (or use Docker)

### Local Development (One Command)

```bash
# 1. Clone and setup
git clone https://github.com/cerform/INKA.git
cd inka

# 2. Copy environment variables
cp .env.example .env
# Edit .env and add your BOT_TOKEN

# 3. Start everything
docker compose up --build
```

**Services will be available at:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Admin Panel: http://localhost:3000
- Bot: Running in polling mode

### Manual Setup (Without Docker)

```bash
# Install Python dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Start PostgreSQL and Redis (or use Docker for these)
docker compose up postgres redis -d

# Run migrations
make migrate

# Start API
uvicorn apps.api.src.main:app --reload

# Start Bot (in another terminal)
python -m apps.bot.src.main

# Start Admin (in another terminal)
cd apps/admin && npm install && npm run dev
```

## 📁 Project Structure

```
inka/
├── apps/
│   ├── api/          # FastAPI backend
│   ├── bot/          # Telegram bot
│   └── admin/        # React admin panel
├── libs/
│   ├── core/         # Shared business logic
│   ├── database/     # DB models + migrations
│   └── observability/# Logging
├── infra/            # Terraform, K8s configs
├── docs/             # Documentation
└── scripts/          # Utility scripts
```

## 🛠 Common Tasks

```bash
make help           # Show all available commands
make test           # Run tests
make lint           # Run linters
make format         # Format code
make migrate        # Run DB migrations
make docker-up      # Start services
make docker-down    # Stop services
```

## 📚 Documentation

- [Architecture](docs/architecture/README.md)
- [Development Setup](docs/development/setup.md)
- [Deployment Guide](docs/operations/deployment.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🔐 Environment Variables

See `.env.example` for all required variables. Key ones:
- `BOT_TOKEN` - Telegram bot token from @BotFather
- `DATABASE_URL` - PostgreSQL connection string
- `API_SECRET_KEY` - Secret for JWT tokens (min 32 chars)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov --cov-report=html

# Run specific test file
pytest apps/api/tests/test_bookings.py
```

## 🚢 Deployment

### Google Cloud Run (Recommended)

```bash
# Deploy API
gcloud run deploy inka-api --source apps/api

# Deploy Bot
gcloud run deploy inka-bot --source apps/bot
```

See [deployment docs](docs/operations/deployment.md) for detailed instructions.

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -m "feat: add my feature"`
3. Run tests: `make test`
4. Run linters: `make lint`
5. Push and create PR

## 📄 License

Proprietary - INKA Tattoo Salon

## 🆘 Support

- Issues: https://github.com/cerform/INKA/issues
- Docs: https://github.com/cerform/INKA/wiki
# INKA
