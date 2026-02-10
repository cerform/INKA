from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from apps.bot.bot.utils.db import get_db
from packages.core.domains.auth.models import User
from packages.core.domains.auth.break_glass import break_glass_service
from packages.core.domains.auth.rbac import has_permission
import uuid

# States for Break-Glass flow
REASON_INPUT = 1

async def qa_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user or not has_permission(user.role, "diag:read"):
            await update.message.reply_text("Access denied.")
            return

        keyboard = [
            [InlineKeyboardButton("System Status", callback_data="qa:status")],
            [InlineKeyboardButton("Reset Test Data", callback_data="qa:reset")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("QA Management Menu:", reply_markup=reply_markup)

async def debug_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user or user.role != "debugger":
            await update.message.reply_text("Access denied. Debuggers only.")
            return

        await update.message.reply_text("Initiating Break-Glass. Please provide a reason for elevation:")
        return REASON_INPUT

async def debug_reason_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        session = break_glass_service.create_session(db, user.id, reason)
        db.commit()

        await update.message.reply_text(
            f"✅ Break-Glass Session Active.\n"
            f"Reason: {reason}\n"
            f"Expires at: {session.expires_at.strftime('%Y-%m-%d %H:%M:%S')} (UTC)\n"
            f"You now have elevated access."
        )
    return ConversationHandler.END

debug_handler = ConversationHandler(
    entry_points=[CommandHandler("debug", debug_start)],
    states={
        REASON_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, debug_reason_received)],
    },
    fallbacks=[],
)
