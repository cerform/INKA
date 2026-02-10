from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from apps.bot.bot.utils.db import get_db
from packages.core.domains.masters.models import Master
from packages.core.domains.clients.models import Client
from packages.core.domains.auth.rbac import has_permission
from packages.core.domains.auth.models import User
import logging

logger = logging.getLogger(__name__)

async def check_admin_permission(update: Update, permission: str) -> bool:
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not user or not has_permission(user.role, permission):
            await update.message.reply_text("⛔ Access denied.")
            return False
    return True

async def list_masters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin_permission(update, "masters:read"):
        return
    
    with get_db() as db:
        masters = db.query(Master).all()
        text = "📋 Masters:\n" + "\n".join([f"- {m.name} ({'Active' if m.active else 'Inactive'})" for m in masters])
        await update.message.reply_text(text)

async def list_clients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin_permission(update, "clients:read"):
        return
    
    with get_db() as db:
        clients = db.query(Client).limit(20).all()
        text = "📋 Clients:\n" + "\n".join([f"- {c.full_name} ({c.phone})" for c in clients])
        await update.message.reply_text(text)

management_handlers = [
    CommandHandler("masters", list_masters),
    CommandHandler("clients", list_clients),
]
