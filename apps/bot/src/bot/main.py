from telegram.ext import ApplicationBuilder, CommandHandler
import logging
import os
import sys
from apps.bot.bot.handlers.booking import booking_handler
from apps.bot.bot.handlers.management import management_handlers
from apps.bot.bot.handlers.support.handlers import qa_menu, debug_handler
from packages.core.logging_config import setup_logging

# Configure standardized JSON logging
setup_logging()

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

async def start(update, context):
    await update.message.reply_text(
        "Welcome to INKA Admin Bot! 🤖\n\n"
        "Available commands:\n"
        "/book - Create a new booking\n"
        "/masters - List all masters\n"
        "/clients - List all clients\n"
        "/cancel - Abort current operation"
    )

def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("qa", qa_menu))
    application.add_handler(debug_handler)
    application.add_handler(booking_handler)
    for handler in management_handlers:
        application.add_handler(handler)
    
    if WEBHOOK_URL:
        logger.info(f"Starting bot with webhook: {WEBHOOK_URL}")
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8080)),
            webhook_url=WEBHOOK_URL,
        )
    else:
        logger.info("Starting bot using polling (Local Dev)")
        application.run_polling()

if __name__ == "__main__":
    main()
