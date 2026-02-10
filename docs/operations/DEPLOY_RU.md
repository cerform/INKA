# 🚀 Быстрый Деплой в Google Cloud Run

## Предварительные Требования

1. **Google Cloud аккаунт** с активной billing
2. **gcloud CLI** установлен ([инструкция](https://cloud.google.com/sdk/docs/install))
3. **Telegram Bot Token** от @BotFather

## Шаг 1: Подготовка

```bash
# Клонировать репозиторий
cd /Users/simanbekov/projects/inka

# Установить gcloud CLI (если еще не установлен)
curl https://sdk.cloud.google.com | bash

# Авторизоваться
gcloud auth login

# Создать новый проект (или использовать существующий)
gcloud projects create inka-prod-123 --name="INKA Production"
gcloud config set project inka-prod-123

# Включить billing
# Перейдите на: https://console.cloud.google.com/billing
```

## Шаг 2: Автоматический Деплой

```bash
# Отредактировать PROJECT_ID в скрипте
nano scripts/deploy.sh
# Измените: PROJECT_ID="your-gcp-project-id" на ваш ID

# Запустить деплой
./scripts/deploy.sh prod
```

**Скрипт автоматически:**
- ✅ Включит необходимые API
- ✅ Создаст Cloud SQL PostgreSQL
- ✅ Настроит Secret Manager
- ✅ Задеплоит API, Bot, Admin Panel
- ✅ Выдаст URL всех сервисов

## Шаг 3: Первоначальная Настройка

После деплоя откройте Setup Wizard:

```
https://inka-admin-xxx.run.app/setup
```

**Введите:**
1. **Bot Token** - получите у @BotFather в Telegram
2. **Database URL** - скопируйте из вывода скрипта
3. **Admin Email** - ваш email
4. **Admin Password** - минимум 8 символов

## Шаг 4: Настройка Telegram Webhook

```bash
# Замените YOUR_BOT_TOKEN и BOT_URL
curl -X POST https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook \
  -d "url=https://inka-bot-xxx.run.app/webhook"
```

## Шаг 5: Проверка

**API:**
```bash
curl https://inka-api-xxx.run.app/health
```

**Bot:**
Отправьте `/start` вашему боту в Telegram

**Admin Panel:**
Откройте `https://inka-admin-xxx.run.app` и войдите

## Управление

### Просмотр Логов

```bash
# API логи
gcloud run services logs read inka-api-prod --region europe-west1 --limit 50

# Bot логи
gcloud run services logs read inka-bot-prod --region europe-west1 --limit 50
```

### Обновление Secrets

```bash
# Обновить Bot Token
echo "new-token" | gcloud secrets versions add bot-token-prod --data-file=-

# Обновить API Secret Key
openssl rand -base64 32 | gcloud secrets versions add api-secret-key-prod --data-file=-
```

### Масштабирование

```bash
# Увеличить количество инстансов API
gcloud run services update inka-api-prod \
  --region europe-west1 \
  --min-instances 2 \
  --max-instances 20
```

### Откат к Предыдущей Версии

```bash
# Посмотреть ревизии
gcloud run revisions list --service inka-api-prod --region europe-west1

# Откатиться
gcloud run services update-traffic inka-api-prod \
  --to-revisions REVISION_NAME=100 \
  --region europe-west1
```

## Стоимость

**Минимальная конфигурация:**
- Cloud SQL (db-f1-micro): ~$7/мес
- Cloud Run (низкий трафик): ~$5/мес
- **Итого: ~$12/мес**

**Production конфигурация:**
- Cloud SQL (db-n1-standard-1): ~$50/мес
- Cloud Run (средний трафик): ~$20/мес
- Cloud Storage: ~$1/мес
- **Итого: ~$71/мес**

## Troubleshooting

### Ошибка: "Permission denied"
```bash
# Добавить роли сервисному аккаунту
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT" \
  --role="roles/run.admin"
```

### Ошибка: "Database connection failed"
```bash
# Проверить Cloud SQL
gcloud sql instances describe inka-db-prod

# Проверить секрет database-url
gcloud secrets versions access latest --secret=database-url-prod
```

### Bot не отвечает
```bash
# Проверить webhook
curl https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo

# Переустановить webhook
curl -X POST https://api.telegram.org/botYOUR_TOKEN/setWebhook \
  -d "url=https://inka-bot-xxx.run.app/webhook"
```

## Полезные Ссылки

- [Cloud Console](https://console.cloud.google.com)
- [Cloud Run Dashboard](https://console.cloud.google.com/run)
- [Cloud SQL Dashboard](https://console.cloud.google.com/sql)
- [Secret Manager](https://console.cloud.google.com/security/secret-manager)
- [Logs Explorer](https://console.cloud.google.com/logs)

## Следующие Шаги

1. ✅ Настроить custom domain (опционально)
2. ✅ Настроить Cloud Monitoring alerts
3. ✅ Настроить автоматические бэкапы Cloud SQL
4. ✅ Настроить CI/CD с GitHub Actions
