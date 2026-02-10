from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from apps.bot.utils.i18n import gettext

def get_main_menu_keyboard(locale: str) -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text=gettext("menu-schedule", locale)),
        types.KeyboardButton(text=gettext("menu-booking", locale))
    )
    builder.row(
        types.KeyboardButton(text=gettext("menu-clients", locale)),
        types.KeyboardButton(text=gettext("menu-staff", locale))
    )
    builder.row(
        types.KeyboardButton(text=gettext("menu-settings", locale))
    )
    return builder.as_markup(resize_keyboard=True)

def get_cancel_keyboard(locale: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=gettext("cancel-button", locale), callback_data="cancel")
    return builder.as_markup()
