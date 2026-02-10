from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from apps.bot.states.booking import BookingStates
from apps.bot.keyboards import booking as kb
from packages.db.session import AsyncSessionLocal
from sqlalchemy import select
from packages.core.models.service import Service
from packages.core.models.master import Master

router = Router()

@router.message(Command("book"))
async def start_booking(message: types.Message, state: FSMContext):
    await state.set_state(BookingStates.selecting_service)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Service))
        services = result.scalars().all()
    
    if not services:
        await message.answer("No services available at the moment.")
        return

    await message.answer("Please select a service:", reply_markup=kb.get_services_keyboard(services)) 

@router.callback_query(BookingStates.selecting_service, F.data.startswith("service_"))
async def process_service(callback_query: types.CallbackQuery, state: FSMContext):
    service_id = int(callback_query.data.split("_")[1])
    await state.update_data(service_id=service_id)
    
    await state.set_state(BookingStates.selecting_master)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Master).where(Master.is_active == True))
        masters = result.scalars().all()
    
    await callback_query.message.edit_text(
        "Please select a master:", 
        reply_markup=kb.get_masters_keyboard(masters)
    )
    await callback_query.answer()

@router.callback_query(BookingStates.selecting_master, F.data.startswith("master_"))
async def process_master(callback_query: types.CallbackQuery, state: FSMContext):
    master_id = int(callback_query.data.split("_")[1])
    await state.update_data(master_id=master_id)
    
    await state.set_state(BookingStates.selecting_date)
    # TODO: Show calendar for date selection
    await callback_query.message.edit_text("Please enter date (YYYY-MM-DD):")
    await callback_query.answer()
