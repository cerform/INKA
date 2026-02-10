from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from apps.bot.utils.i18n import gettext
from apps.bot.keyboards.base import get_cancel_keyboard
from apps.bot.states.booking import ClientStates

router = Router()

@router.message(lambda message: message.text in [gettext("menu-clients", "en"), gettext("menu-clients", "ru")])
async def menu_clients(message: types.Message, locale: str):
    await message.answer(
        gettext("menu-clients", locale),
        # Placeholder for client list keyboard
    )

@router.message(lambda message: message.text in [gettext("menu-staff", "en"), gettext("menu-staff", "ru")])
async def menu_staff(message: types.Message, locale: str):
    await message.answer(
        gettext("menu-staff", locale),
        # Placeholder for staff management keyboard
    )
