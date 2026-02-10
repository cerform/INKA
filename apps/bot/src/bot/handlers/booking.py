from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from apps.bot.bot.states import BookingState
from apps.bot.bot.utils.db import get_db
from packages.core.domains.masters.models import Master
from packages.core.domains.clients.models import Client
from packages.core.domains.bookings.service import booking_service
from packages.core.domains.auth.models import User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    with get_db() as db:
        masters = db.query(Master).filter(Master.active == True).all()
        if not masters:
            await update.message.reply_text("No active masters available.")
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton(m.name, callback_data=f"master:{m.id}")]
            for m in masters
        ]
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select a master:", reply_markup=reply_markup)
        return BookingState.MASTER_SELECT

async def master_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("Booking cancelled.")
        return ConversationHandler.END

    master_id = query.data.split(":")[1]
    context.user_data["master_id"] = master_id
    
    with get_db() as db:
        clients = db.query(Client).limit(10).all() # Simple search logic pending
        keyboard = [
            [InlineKeyboardButton(c.full_name, callback_data=f"client:{c.id}")]
            for c in clients
        ]
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select a client:", reply_markup=reply_markup)
        return BookingState.CLIENT_SELECT

async def client_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("Booking cancelled.")
        return ConversationHandler.END

    client_id = query.data.split(":")[1]
    context.user_data["client_id"] = client_id
    
    await query.edit_message_text("Enter date and time (YYYY-MM-DD HH:MM):")
    return BookingState.TIME_SELECT

async def time_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time_str = update.message.text
    try:
        start_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        # Logic for end_time (e.g., +1 hour)
        from datetime import timedelta
        end_time = start_time + timedelta(hours=1)
        
        context.user_data["start_time"] = start_time
        context.user_data["end_time"] = end_time
        
        await update.message.reply_text(
            f"Confirm booking for {time_str}?\nType 'yes' to confirm or 'cancel' to abort."
        )
        return BookingState.CONFIRM
    except ValueError:
        await update.message.reply_text("Invalid format. Please use YYYY-MM-DD HH:MM.")
        return BookingState.TIME_SELECT

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text.lower() != "yes":
        await update.message.reply_text("Booking aborted.")
        return ConversationHandler.END

    with get_db() as db:
        # Mock actor for now - should come from session/middleware
        actor = db.query(User).filter(User.telegram_id == update.effective_user.id).first()
        if not actor:
            await update.message.reply_text("User error. Not registered.")
            return ConversationHandler.END

        class Data: pass
        data = Data()
        data.master_id = context.user_data["master_id"]
        data.client_id = context.user_data["client_id"]
        data.start_time = context.user_data["start_time"]
        data.end_time = context.user_data["end_time"]

        try:
            booking_service.create_booking(db, data, actor)
            db.commit()
            await update.message.reply_text("✅ Booking created successfully!")
        except ValueError as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        
    return ConversationHandler.END

booking_handler = ConversationHandler(
    entry_points=[CommandHandler("book", start_booking)],
    states={
        BookingState.MASTER_SELECT: [CallbackQueryHandler(master_selected)],
        BookingState.CLIENT_SELECT: [CallbackQueryHandler(client_selected)],
        BookingState.TIME_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_entered)],
        BookingState.CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_booking)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
)
