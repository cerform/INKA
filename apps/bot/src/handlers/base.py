from aiogram import Router, types
from aiogram.filters import Command
from apps.bot.utils.i18n import gettext
from apps.bot.keyboards.base import get_main_menu_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, locale: str):
    await message.answer(
        gettext("welcome-message", locale),
        reply_markup=get_main_menu_keyboard(locale)
    )

@router.message(lambda message: message.text in [gettext("menu-schedule", "en"), gettext("menu-schedule", "ru")])
async def menu_schedule(message: types.Message, locale: str):
    # This is a placeholder for the actual schedule view
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    await message.answer(
        gettext("schedule-today", locale, date=today) + "\n\n" + gettext("schedule-empty", locale)
    )
