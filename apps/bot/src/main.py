from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from redis.asyncio import Redis
from packages.core.config import settings

# Observability
import os
from packages.observability import setup_logging, setup_sentry, get_logger

# NOTE: Booking handler disabled to avoid mixed model imports at startup.
# Re-enable after consolidating SQLAlchemy models.
from apps.bot.middlewares.i18n import I18nMiddleware

# --- Observability init ---
setup_logging(
    log_level=getattr(settings, "LOG_LEVEL", "INFO"),
    environment=getattr(settings, "ENVIRONMENT", "development"),
    service_name="inka-bot",
)
setup_sentry(
    dsn=os.environ.get("SENTRY_DSN", ""),
    environment=getattr(settings, "ENVIRONMENT", "development"),
    version=getattr(settings, "VERSION", "0.1.0"),
)

logger = get_logger("inka-bot")

# Initialize Bot and Dispatcher
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

# Storage for FSM
redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
storage = RedisStorage(redis, key_builder=DefaultKeyBuilder(with_destiny=True))

dp = Dispatcher(storage=storage)

# Register Middlewares
dp.message.middleware(I18nMiddleware())
dp.callback_query.middleware(I18nMiddleware())

# Register Routers
# dp.include_router(booking.router)
from apps.bot.handlers.orchestrator import orchestrator_router
from apps.bot.handlers.defects import router as defects_router
dp.include_router(orchestrator_router)
dp.include_router(defects_router)

import asyncio
from aiohttp import web

async def start_bot():
    logger.info("Starting Telegram Bot (Polling)")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

async def health_check(request):
    return web.Response(text="OK")

async def run_services():
    # Setup dummy web server for Cloud Run port check
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    
    await asyncio.gather(
        site.start(),
        start_bot()
    )

if __name__ == "__main__":
    asyncio.run(run_services())

