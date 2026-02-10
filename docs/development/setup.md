# Development Setup

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop
- Git
- Code editor (VS Code recommended)

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/cerform/INKA.git
cd inka
```

### 2. Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set:
- `BOT_TOKEN` - Get from @BotFather on Telegram
- `API_SECRET_KEY` - Generate with: `openssl rand -base64 32`

### 3. Install Dependencies

```bash
# Python dependencies
pip install -e .[dev]

# Node dependencies (for admin panel)
cd apps/admin && npm install && cd ../..

# Pre-commit hooks
pre-commit install
```

## Running Locally

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker compose up --build

# Services will be available at:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Admin: http://localhost:3000
# - Bot: Running in polling mode
```

### Option 2: Manual (For Development)

```bash
# Terminal 1: Start PostgreSQL and Redis
docker compose up postgres redis

# Terminal 2: Run migrations
alembic -c libs/database/alembic.ini upgrade head

# Terminal 3: Start API
uvicorn apps.api.src.main:app --reload --port 8000

# Terminal 4: Start Bot
python -m apps.bot.src.main

# Terminal 5: Start Admin
cd apps/admin && npm run dev
```

## Project Structure

```
inka/
├── apps/
│   ├── api/          # FastAPI backend
│   │   ├── src/
│   │   │   ├── main.py         # Entry point
│   │   │   └── app/
│   │   │       ├── domains/    # API routes by domain
│   │   │       └── deps/       # Dependencies (auth, db)
│   │   └── tests/
│   ├── bot/          # Telegram bot
│   │   ├── src/
│   │   │   ├── main.py         # Entry point
│   │   │   └── bot/
│   │   │       ├── handlers/   # Command handlers
│   │   │       └── states.py   # Conversation states
│   │   └── tests/
│   └── admin/        # React admin panel
│       └── src/
├── libs/             # Shared libraries
│   ├── core/         # Business logic
│   │   └── src/
│   │       └── domains/        # DDD domains
│   ├── database/     # DB models + migrations
│   │   ├── src/
│   │   └── alembic/
│   └── observability/# Logging
└── docs/             # Documentation
```

## Common Tasks

### Running Tests

```bash
# All tests
pytest

# Specific service
pytest apps/api/tests/
pytest apps/bot/tests/

# With coverage
pytest --cov --cov-report=html
open htmlcov/index.html
```

### Code Quality

```bash
# Run linters
make lint

# Auto-format code
make format

# Type checking
mypy apps/ libs/
```

### Database Migrations

```bash
# Create new migration
make migrate-create MSG="add user table"

# Apply migrations
make migrate

# Rollback one migration
alembic -c libs/database/alembic.ini downgrade -1
```

### Adding Dependencies

```bash
# Python (edit pyproject.toml, then)
pip install -e .[dev]

# Node (in apps/admin/)
npm install package-name
```

## IDE Setup (VS Code)

### Recommended Extensions

- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)
- ESLint (dbaeumer.vscode-eslint)
- Prettier (esbenp.prettier-vscode)

### Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## Debugging

### API

```bash
# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn apps.api.src.main:app --reload
```

### Bot

```bash
# Run with debugger
python -m debugpy --listen 5679 --wait-for-client -m apps.bot.src.main
```

## Troubleshooting

### Import errors

```bash
# Reinstall in editable mode
pip install -e .[dev]
```

### Database connection errors

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check connection
psql postgresql://inka:inka@localhost:5432/inka_dev
```

### Port already in use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 PID
```

## Next Steps

- Read [Architecture](../architecture/README.md)
- Check [Contributing Guidelines](CONTRIBUTING.md)
- Review [API Documentation](http://localhost:8000/docs)
