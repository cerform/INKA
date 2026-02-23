# 🤖 Телеграм Бот INKA - Развёртывание, Конфигурация и Управление

## 📍 Текущее развёртывание

### Deployed Service Information
```
URL:        https://tattoo-bot-408800151466.europe-west1.run.app/
Service:    inka-bot
Region:     europe-west1
Project:    tattoo-480007 (GCP)
Image:      gcr.io/tattoo-480007/inka-bot:latest
Platform:   Google Cloud Run
```

### Git Revision (Текущая версия кода)
```
Commit SHA:     d9257f89abead8ea2ae098018426c68df2c8de4a (full)
Commit Short:   d9257f8
Branch:         main
Message:        feat: Establish release management, quality gating, and chaos 
                engineering frameworks with new scripts, libraries, CI/CD 
                workflows, and documentation.
Date:           2026-02-22 09:29:01 +0200
```

### Repository Source
```
Repository:     https://github.com/cerform/INKA.git
Type:           Monorepo (многопроектный репозиторий)
Structure:      INKA Project
                ├── apps/bot/          ← Код телеграм бота
                ├── apps/api/          ← API сервер
                ├── apps/admin/        ← Админ панель (React)
                ├── libs/core/         ← Общие библиотеки
                ├── docs/              ← Документация
                └── scripts/           ← Deploy scripts
```

---

## 🔧 Структура Телеграм Бота

### Bot Entry Point
**Местоположение**: `apps/bot/src/main.py`

```python
# Bot инициализируется с токеном из переменной окружения
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

# FSM Storage - Redis для хранения состояний
redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
storage = RedisStorage(redis, key_builder=DefaultKeyBuilder(with_destiny=True))

# Dispatcher обрабатывает команды и сообщения
dp = Dispatcher(storage=storage)

# Активные роутеры (handlers):
# - orchestrator_router  (оркестрирование)
# - defects_router       (управление дефектами)
```

### Handler Files
```
apps/bot/src/handlers/
├── orchestrator.py      ← Основная логика оркестрирования
├── defects.py          ← Управление дефектами
├── booking.py          ← Букинги (временно отключен)
├── management.py       ← Управленческие команды
├── support/
│   └── handlers.py     ← QA и поддержка
└── chaos_handler.py    ← Chaos engineering команды
```

### Middleware & Services
```
apps/bot/src/
├── middlewares/
│   └── i18n.py         ← Интернационализация (многоязычность)
├── services/
│   ├── llm.py          ← Интеграция с LLM (OpenAI)
│   ├── quality.py      ← Quality assessment
│   └── orchestrator.py ← Оркестрирование задач
└── config.py           ← Конфигурация бота
```

---

## 🔐 Конфигурация Телеграм Бота

### 1️⃣ Получение Bot Token от Telegram

#### Шаг 1: Свяжитесь с @BotFather
```
1. Откройте Telegram
2. Найдите @BotFather
3. Отправьте команду /start
```

#### Шаг 2: Создайте новый бот
```
Команда:  /newbot
Ответьте на вопросы:
- Как назвать бота? → "INKA Tattoo Bot" (или свое название)
- Какой будет username? → "inka_tattoo_bot" (должен заканчиваться на _bot)

Результат: Получите токен вида
123456789:ABCdefGHIjklMNOpqrsTUVwxyzABCdefGHI
```

#### Шаг 3: Сохраните токен
```bash
# В .env файл
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyzABCdefGHI
```

### 2️⃣ Переменные окружения для бота

**Файл**: `.env` или Secret Manager в GCP

#### Обязательные переменные
```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyzABCdefGHI

# Database
DATABASE_URL=postgresql://user:password@host:5432/inka_db

# Redis (для FSM storage)
REDIS_HOST=redis
REDIS_PORT=6379

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

#### Optional переменные
```bash
# Webhook (если используется webhook вместо polling)
TELEGRAM_WEBHOOK_URL=https://tattoo-bot-408800151466.europe-west1.run.app/webhook
TELEGRAM_WEBHOOK_SECRET=your_secret_here

# Для Future LLM интеграции
OPENAI_API_KEY=sk-...your_openai_key...
```

### 3️⃣ Настройка Webhook (если нужна HTTPS)

```bash
# Установить webhook для получения обновлений через HTTPS
curl -X POST "https://api.telegram.org/bot123456789:ABCdefGHIjklMNOpqrsTUVwxyzABCdefGHI/setWebhook" \
  -d "url=https://tattoo-bot-408800151466.europe-west1.run.app/webhook" \
  -d "secret_token=your_secret_here"

# Проверить статус
curl "https://api.telegram.org/bot123456789:ABCdefGHIjklMNOpqrsTUVwxyzABCdefGHI/getWebhookInfo"

# Удалить webhook (вернуться к polling)
curl -X POST "https://api.telegram.org/bot123456789:ABCdefGHIjklMNOpqrsTUVwxyzABCdefGHI/deleteWebhook"
```

### 4️⃣ Управление в Cloud Run (GCP)

#### Обновить Bot Token
```bash
# Через gcloud CLI
echo -n "NEW_BOT_TOKEN" | gcloud secrets versions add inka-bot-token --data-file=-

# Пересоздать сервис
gcloud run deploy inka-bot \
  --region europe-west1 \
  --set-secrets="TELEGRAM_BOT_TOKEN=inka-bot-token:latest"
```

#### Просмотреть текущие настройки
```bash
gcloud run services describe inka-bot --region europe-west1
```

#### Обновить переменные окружения
```bash
gcloud run services update inka-bot \
  --region europe-west1 \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO"
```

---

## 🤖 Конфигурация LLM (OpenAI)

### Текущее состояние
- ✅ Infrastructure ready (конфиг файлы созданы)
- ⏱️ Implementation pending (интеграция в разработке)

### Местоположение LLM config
**Файлы конфигурации**:
```
libs/core/src/config.py         ← OPENAI_API_KEY проходит здесь
apps/bot/src/services/llm.py    ← LLM сервис (если существует)
```

### 1️⃣ Получение OpenAI API Key

```
1. Зайдите на https://platform.openai.com/api-keys
2. Нажмите "Create new secret key"
3. Скопируйте ключ (он появится только один раз!)
4. Сохраните в безопасном месте
```

Ключ должен выглядеть как: `sk-xxxxxxxxxxxxxxxxxxxx...`

### 2️⃣ Установка в Cloud Run

```bash
# Создать secret
echo -n "sk-your_openai_key_here" | gcloud secrets create openai-api-key --data-file=-

# Или обновить существующий
echo -n "sk-your_openai_key_here" | gcloud secrets versions add openai-api-key --data-file=-

# Развернуть с secret
gcloud run deploy inka-bot \
  --region europe-west1 \
  --set-secrets="OPENAI_API_KEY=openai-api-key:latest"
```

### 3️⃣ Переменные окружения LLM

```bash
# Обязательно
OPENAI_API_KEY=sk-your_key_here

# Optional (если не указано, используются defaults)
OPENAI_MODEL=gpt-4-turbo            # или gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7              # 0-1, влияет на креативность
OPENAI_MAX_TOKENS=2048              # Максимальная длина ответа
```

### 4️⃣ Конфиг файл для LLM

**Файл**: `libs/core/src/config.py`

```python
class Settings(BaseSettings):
    # ... другие варианты ...
    
    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2048
    
    # Если используется Azure OpenAI
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
```

### 5️⃣ Примеры использования LLM в handlers

**Когда будет готово**:

```python
# apps/bot/src/handlers/your_handler.py
from apps.bot.services.llm import LLMService

llm = LLMService()

# Пример: генерация описания работы
response = await llm.generate(
    prompt="Опишите стиль татуировки: минимализм",
    temperature=0.7,
    max_tokens=500
)

# Пример: анализ качества
quality_assessment = await llm.analyze_quality(
    work_description="Черно-белая минималистичная линия на запястье",
    model="gpt-4-turbo"
)
```

---

## 📋 Environment Variables Для Всего Проекта

### Bot Service (inka-bot)
```bash
# Secrets (из Secret Manager)
TELEGRAM_BOT_TOKEN=123456789:ABC...
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...

# Env vars
ENVIRONMENT=production
LOG_LEVEL=INFO
REDIS_HOST=redis
REDIS_PORT=6379
TELEGRAM_WEBHOOK_URL=https://tattoo-bot-408800151466.europe-west1.run.app/webhook
```

### API Service (inka-api)
```bash
SECRET_KEY=your_32_char_secret_key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Admin Service (inka-admin)
```bash
VITE_API_URL=https://inka-api-408800151466.europe-west1.run.app
ENVIRONMENT=production
```

---

## 🚀 Развёртывание изменений

### Автоматическое (CI/CD)
```bash
# Просто push в main branch
git add .
git commit -m "feat: update bot configuration"
git push origin main

# GitHub Actions автоматически:
# 1. Собирает image
# 2. Пушит в GCR (Google Container Registry)
# 3. Разворачивает в Cloud Run
```

### Ручное развёртывание
```bash
# Build и push image
gcloud builds submit --tag gcr.io/tattoo-480007/inka-bot:latest \
  --dockerfile apps/bot/Dockerfile

# Deploy на Cloud Run
gcloud run deploy inka-bot \
  --image gcr.io/tattoo-480007/inka-bot:latest \
  --region europe-west1 \
  --set-secrets TELEGRAM_BOT_TOKEN=inka-bot-token:latest
```

---

## 📊 Логирование и Мониторинг

### Просмотр логов в Cloud Run
```bash
# Последние логи
gcloud run services logs read inka-bot --region europe-west1 --limit 50

# Живой поток логов
gcloud run services logs read inka-bot --region europe-west1 --follow
```

### Уровни логирования
```bash
# Изменить уровень логирования
gcloud run services update inka-bot --region europe-west1 \
  --set-env-vars LOG_LEVEL=DEBUG

# Возможные значения: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## 🔍 Диагностика проблем

### Бот не отвечает
```bash
# 1. Проверить статус сервиса
gcloud run services describe inka-bot --region europe-west1

# 2. Посмотреть последние логи
gcloud run services logs read inka-bot --region europe-west1 --limit 100

# 3. Проверить токен
gcloud secrets versions list inka-bot-token

# 4. Проверить webhook статус
curl "https://api.telegram.org/bot$TOKEN/getWebhookInfo"
```

### LLM не работает
```bash
# 1. Проверить ключ OpenAI
gcloud secrets versions list openai-api-key

# 2. Включить DEBUG логирование
gcloud run services update inka-bot --region europe-west1 \
  --set-env-vars LOG_LEVEL=DEBUG

# 3. Проверить квоту OpenAI на https://platform.openai.com/account/billing
```

### Database connection issues
```bash
# 1. Проверить DATABASE_URL
gcloud secrets versions access latest --secret="database-url"

# 2. Проверить Cloud SQL proxy
gcloud sql instances describe inka-db

# 3. Убедиться что Cloud Run имеет доступ
gcloud sql instances patch inka-db --require-ssl=false
```

---

## 📚 Дополнительные ресурсы

### Документация
- [Deployment Guide](./docs/operations/deployment.md)
- [Development Setup](./docs/development/setup.md)
- [Russian Deploy Guide](./docs/operations/DEPLOY_RU.md)

### Ссылки
- GitHub Repo: https://github.com/cerform/INKA.git
- Telegram BotFather: https://t.me/BotFather
- OpenAI API: https://platform.openai.com
- Google Cloud Console: https://console.cloud.google.com

### Команды для быстрого доступа
```bash
# Просмотреть все сервисы
gcloud run services list --region europe-west1

# Просмотреть все secrets
gcloud secrets list

# Описание bot service
gcloud run services describe inka-bot --region europe-west1

# Описание database
gcloud sql instances describe inka-db
```

---

## Summary

| Компонент | Статус | Конфиг |
|-----------|--------|--------|
| **Bot Service** | ✅ Deployed | Cloud Run |
| **API Service** | ✅ Deployed | Cloud Run |
| **Admin Panel** | ✅ Deployed | Cloud Run |
| **Database** | ✅ Running | Cloud SQL (PostgreSQL) |
| **Redis** | ✅ Running | Cloud Memorystore |
| **Telegram Bot** | ✅ Active | Polling mode |
| **LLM (OpenAI)** | ⏱️ Ready to configure | Requires OPENAI_API_KEY |

**Текущая версия кода**: `d9257f8` (2026-02-22)
**Последний коммит**: feat: Establish release management, quality gating, and chaos engineering frameworks

---

**Дата создания**: 2026-02-22
**Обновлено**: 2026-02-22
**Версия**: 1.0
