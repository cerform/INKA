from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from redis.asyncio import Redis
from packages.core.config import settings
from apps.bot.handlers import booking
from apps.bot.middlewares.i18n import I18nMiddleware

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
dp.include_router(booking.router)
from apps.bot.handlers.orchestrator import orchestrator_router
dp.include_router(orchestrator_router)

async def start_bot():
    print("Starting Telegram Bot...")
    # await bot.delete_webhook(drop_pending_updates=True)
    # await dp.start_polling(bot)
    # For Production, we use Webhooks in FastAPI lifespan
    pass

async def set_webhook():
    if settings.TELEGRAM_WEBHOOK_URL:
        await bot.set_webhook(url=str(settings.TELEGRAM_WEBHOOK_URL))
