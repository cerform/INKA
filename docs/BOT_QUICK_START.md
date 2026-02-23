# 🚀 Quick Start Guide - Bot Configuration & LLM Setup

## Current Deployment Status

### Bot Service
- **URL**: https://tattoo-bot-408800151466.europe-west1.run.app/
- **Image**: `gcr.io/tattoo-480007/inka-bot:latest`
- **Git Commit**: `d9257f8` (feat: release management & chaos engineering)
- **Date**: 2026-02-22 09:29:01 +0200
- **Region**: europe-west1 (GCP)

---

## Quick Configuration Checklist

### Configure Telegram Bot Token

1. **Get Token from @BotFather**:
   ```
   1. Open Telegram → @BotFather
   2. /newbot → follow prompts
   3. Copy the token: 123456789:ABCdefGHI...
   ```

2. **Set in GCP Secret Manager**:
   ```bash
   # Create or update
   echo -n "123456789:ABCdefGHI..." | \
     gcloud secrets versions add inka-bot-token --data-file=-
   
   # Redeploy service
   gcloud run deploy inka-bot \
     --region europe-west1 \
     --set-secrets="TELEGRAM_BOT_TOKEN=inka-bot-token:latest"
   ```

3. **Verify**:
   ```bash
   curl "https://api.telegram.org/bot123456789:ABCdefGHI.../getMe"
   ```

---

### Configure OpenAI LLM Integration

1. **Get API Key**:
   - Visit: https://platform.openai.com/api-keys
   - Create new secret key
   - Copy: `sk-xxxxxx...`

2. **Set in GCP Secret Manager**:
   ```bash
   # Create secret
   echo -n "sk-xxxxxx..." | \
     gcloud secrets create openai-api-key --data-file=-
   
   # Or update if exists
   echo -n "sk-xxxxxx..." | \
     gcloud secrets versions add openai-api-key --data-file=-
   ```

3. **Deploy with LLM Key**:
   ```bash
   gcloud run deploy inka-bot \
     --region europe-west1 \
     --set-secrets="OPENAI_API_KEY=openai-api-key:latest"
   ```

4. **Set LLM Parameters** (optional):
   ```bash
   gcloud run services update inka-bot \
     --region europe-west1 \
     --set-env-vars="OPENAI_MODEL=gpt-4-turbo,OPENAI_TEMPERATURE=0.7"
   ```

---

## Environment Variables Reference

### Required for Bot
```bash
TELEGRAM_BOT_TOKEN       # From @BotFather
DATABASE_URL            # PostgreSQL connection
REDIS_HOST             # Redis host (usually redis)
REDIS_PORT             # Redis port (usually 6379)
ENVIRONMENT            # production/staging/development
```

### Optional but Recommended
```bash
OPENAI_API_KEY         # For LLM features (sk-...)
OPENAI_MODEL           # gpt-4-turbo or gpt-3.5-turbo
OPENAI_TEMPERATURE     # 0-1 (default: 0.7)
LOG_LEVEL              # DEBUG/INFO/WARNING/ERROR
```

### Webhook Configuration (if not using polling)
```bash
TELEGRAM_WEBHOOK_URL   # https://your-bot-url/webhook
TELEGRAM_WEBHOOK_SECRET # Random secret string
```

---

## Repository Structure

```
INKA Project (monorepo)
├── apps/
│   ├── bot/           ← Telegram Bot
│   │   └── src/
│   │       ├── main.py          ← Entry point
│   │       ├── handlers/        ← Command handlers
│   │       ├── services/        ← LLM, quality, orchestrator
│   │       └── middlewares/     ← i18n, auth, etc
│   ├── api/           ← FastAPI Server
│   └── admin/         ← React Admin Panel
├── libs/
│   └── core/src/config.py  ← Settings & env vars
├── docs/              ← Documentation
└── scripts/           ← Deployment scripts
```

### Bot Handlers
```
apps/bot/src/handlers/
├── orchestrator.py    → Main orchestration logic
├── defects.py         → Defect management
├── chaos_handler.py   → Chaos engineering commands
├── booking.py         → Booking management (disabled)
├── management.py      → Management commands
└── support/handlers.py → QA & support
```

---

## Common Commands

### View Service Status
```bash
gcloud run services describe inka-bot --region europe-west1
```

### View Recent Logs
```bash
gcloud run services logs read inka-bot --region europe-west1 --limit 50
```

### UpdateEnvironment Variables
```bash
gcloud run services update inka-bot --region europe-west1 \
  --set-env-vars="LOG_LEVEL=DEBUG,ENVIRONMENT=staging"
```

### Check Bot Health
```bash
# Health endpoint
curl https://tattoo-bot-408800151466.europe-west1.run.app/health

# Verify bot token
curl "https://api.telegram.org/bot$TOKEN/getMe"
```

### Live Logs Stream
```bash
gcloud run services logs read inka-bot --region europe-west1 --follow
```

---

## Troubleshooting

### Bot Token Issues
```bash
# Verify token format
# Should be: NUMBER:STRING
# Example: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Test token
curl "https://api.telegram.org/botYOUR_TOKEN/getMe"

# If 401 or 400: token is invalid or expired
# Get new token from @BotFather
```

### LLM Not Working
```bash
# Check OpenAI API key is set
gcloud run services describe inka-bot --region europe-west1 | grep OPENAI

# Check API key is valid (requires billing info on OpenAI)
# Check quota: https://platform.openai.com/account/billing/overview

# Enable DEBUG logging
gcloud run services update inka-bot --region europe-west1 \
  --set-env-vars="LOG_LEVEL=DEBUG"

# View error logs
gcloud run services logs read inka-bot --region europe-west1 --limit 100
```

### Database Connection Issues
```bash
# Verify DATABASE_URL is set
gcloud secrets versions access latest --secret="database-url"

# Check Cloud SQL is running
gcloud sql instances describe inka-db

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

---

## Git Information

**Repository**: https://github.com/cerform/INKA.git
**Current Commit**: `d9257f8`
**Full SHA**: `d9257f89abead8ea2ae098018426c68df2c8de4a`
**Commit Message**: feat: Establish release management, quality gating, and chaos engineering frameworks
**Timestamp**: 2026-02-22 09:29:01 +0200

### To get latest code:
```bash
cd /Users/simanbekov/projects/inka
git pull origin main
git log --oneline -5  # See recent commits
```

---

## Deployment Methods

### Automatic (Recommended)
```bash
# Just push to main - GitHub Actions handles everything
git add .
git commit -m "feat: update bot"
git push origin main
```

### Manual Deployment
```bash
# Build image
gcloud builds submit --tag gcr.io/tattoo-480007/inka-bot:latest \
  --dockerfile apps/bot/Dockerfile

# Deploy
gcloud run deploy inka-bot \
  --image gcr.io/tattoo-480007/inka-bot:latest \
  --region europe-west1
```

---

## Next Steps

1. ✅ Get Telegram Bot Token from @BotFather
2. ✅ Configure TELEGRAM_BOT_TOKEN in GCP Secret Manager
3. ✅ Get OpenAI API Key from https://platform.openai.com
4. ✅ Configure OPENAI_API_KEY in GCP Secret Manager
5. ✅ Redeploy bot service with new secrets
6. ✅ Test bot responding correctly
7. ✅ Monitor logs for errors

---

## Support & Documentation

- Full configuration guide: [BOT_CONFIGURATION_RU.md](./BOT_CONFIGURATION_RU.md) (Russian)
- Development setup: [docs/development/setup.md](./development/setup.md)
- Deployment guide: [docs/operations/deployment.md](./operations/deployment.md)
- API Documentation: Available at `/docs` endpoint when API is running

**Last Updated**: 2026-02-22  
**Version**: 1.0
