from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from packages.core.models.service import Service
from packages.core.models.master import Master
from typing import List

def get_services_keyboard(services: List[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for service in services:
        builder.button(text=f"{service.name} ({service.price}₪)", callback_data=f"service_{service.id}")
    builder.adjust(1)
    return builder.as_markup()

def get_masters_keyboard(masters: List[Master]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for master in masters:
        # Assuming master.user exists and has a full_name
        name = master.user.full_name if master.user else "Unknown Master"
        builder.button(text=name, callback_data=f"master_{master.id}")
    builder.adjust(2)
    return builder.as_markup()

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirm", callback_data="confirm_booking")
    builder.button(text="❌ Cancel", callback_data="cancel_booking")
    return builder.as_markup()
