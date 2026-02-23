from typing import Any, Dict
from uuid import UUID
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.bot.states.defects import DefectReportStates
from packages.db.session import AsyncSessionLocal
from packages.core.domains.defects.models import Defect, DefectSeverity, DefectStatus, ImpactArea, DetectedBy
from packages.core.domains.defects.schemas import DefectCreate, DefectUpdate
from packages.core.domains.defects import service
# Note: service functions I wrote are sync. For the bot, we might need a wrapper or use run_in_executor.
# However, many bot handlers in this repo seem to do direct DB work anyway.
# I'll implement async versions or direct logic for the bot handlers since they use AsyncSession.

router = Router()

def role_required(roles: list):
    """Simple decorator for role checks in bot handlers."""
    def decorator(func):
        async def wrapper(message: types.Message, db_user: Any, *args, **kwargs):
            if db_user.role not in roles and db_user.role != "admin":
                await message.answer("🚫 You don't have permission to use this command.")
                return
            return await func(message, db_user, *args, **kwargs)
        return wrapper
    return decorator

@router.message(Command("incident"))
async def incident_base(message: types.Message, command: CommandObject, db_user: Any):
    if not command.args:
        await message.answer(
            "Usage:\n"
            "/incident report - Multi-step report\n"
            "/incident list_open - List open defects\n"
            "/incident status {uuid} - Get defect details\n"
            "/incident escalate {uuid} - Escalate defect\n"
            "/incident timeline {uuid} - Get defect timeline"
        )
        return

    subcommand = command.args.split()[0].lower()
    
    if subcommand == "report":
        await start_report(message, db_user)
    elif subcommand == "list_open":
        await list_open_defects(message, db_user)
    elif subcommand == "status":
        await get_defect_status(message, command, db_user)
    elif subcommand == "escalate":
        await escalate_defect(message, command, db_user)
    elif subcommand == "timeline":
        await get_defect_timeline(message, command, db_user)
    else:
        await message.answer(f"Unknown subcommand: {subcommand}")

# --- FSM Flow for Reporting ---

async def start_report(message: types.Message, db_user: Any, state: FSMContext = None):
    # This might be called from CommandHandler which doesn't automatically pass state if not using it in signature
    # But aiogram dispatcher usually does.
    if state:
        await state.set_state(DefectReportStates.waiting_for_title)
        await message.answer("Please enter a short title for the defect:")

@router.message(DefectReportStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(DefectReportStates.waiting_for_description)
    await message.answer("Please enter a detailed description (or /skip):")

@router.message(DefectReportStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    description = None if message.text == "/skip" else message.text
    await state.update_data(description=description)
    await state.set_state(DefectReportStates.waiting_for_severity)
    
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="S1 - Critical"), types.KeyboardButton(text="S2 - High")],
            [types.KeyboardButton(text="S3 - Medium"), types.KeyboardButton(text="S4 - Low")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Select severity:", reply_markup=kb)

@router.message(DefectReportStates.waiting_for_severity)
async def process_severity(message: types.Message, state: FSMContext):
    sev_map = {"S1": "S1", "S2": "S2", "S3": "S3", "S4": "S4"}
    sev_key = message.text.split()[0]
    if sev_key not in sev_map:
        await message.answer("Please select using the buttons.")
        return
        
    await state.update_data(severity=sev_map[sev_key])
    await state.set_state(DefectReportStates.waiting_for_impact_area)
    
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="bot"), types.KeyboardButton(text="backend")],
            [types.KeyboardButton(text="db"), types.KeyboardButton(text="security"), types.KeyboardButton(text="devops")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Select impact area:", reply_markup=kb)

@router.message(DefectReportStates.waiting_for_impact_area)
async def process_impact(message: types.Message, state: FSMContext, db_user: Any):
    impact = message.text.lower()
    if impact not in ["bot", "backend", "db", "security", "devops"]:
        await message.answer("Please select using the buttons.")
        return
        
    data = await state.get_data()
    await state.clear()
    
    # Create defect
    async with AsyncSessionLocal() as db:
        # Since service functions are sync, we'll do the logic here or wrap them
        # For simplicity and given standard practices in this repo, direct DB work:
        new_defect = Defect(
            title=data['title'],
            description=data['description'],
            severity=DefectSeverity(data['severity']),
            impact_area=ImpactArea(impact),
            detected_by=DetectedBy.USER,
            environment="prod", # Default for bot reporting
            actor_id=db_user.id,
            status=DefectStatus.OPEN
        )
        db.add(new_defect)
        await db.commit()
        await db.refresh(new_defect)
        
        # Add event
        from packages.core.domains.defects.models import DefectEvent
        event = DefectEvent(
            defect_id=new_defect.id,
            event_type="defect_created",
            actor_id=db_user.id,
            payload={"source": "telegram_bot"}
        )
        db.add(event)
        await db.commit()

    await message.answer(
        f"✅ Defect reported successfully!\n"
        f"ID: <code>{new_defect.id}</code>\n"
        f"Status: open",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )

# --- Subcommands ---

async def list_open_defects(message: types.Message, db_user: Any):
    async with AsyncSessionLocal() as db:
        stmt = select(Defect).where(Defect.status == DefectStatus.OPEN).order_by(Defect.created_at.desc()).limit(10)
        result = await db.execute(stmt)
        defects = result.scalars().all()
        
    if not defects:
        await message.answer("No open defects found.")
        return
        
    text = "📂 <b>Open Defects:</b>\n\n"
    for d in defects:
        text += f"• <code>{str(d.id)[:8]}</code> | {d.severity.value} | {d.title}\n"
        
    await message.answer(text, parse_mode="HTML")

async def get_defect_status(message: types.Message, command: CommandObject, db_user: Any):
    args = command.args.split()
    if len(args) < 2:
        await message.answer("Usage: /incident status {uuid}")
        return
    
    try:
        defect_id = UUID(args[1])
    except ValueError:
        await message.answer("Invalid UUID format.")
        return

    async with AsyncSessionLocal() as db:
        stmt = select(Defect).where(Defect.id == defect_id)
        result = await db.execute(stmt)
        defect = result.scalar_one_or_none()
        
    if not defect:
        await message.answer("Defect not found.")
        return
        
    text = (
        f"📋 <b>Defect Details</b>\n"
        f"ID: <code>{defect.id}</code>\n"
        f"Title: {defect.title}\n"
        f"Status: {defect.status.value}\n"
        f"Severity: {defect.severity.value}\n"
        f"Area: {defect.impact_area.value}\n"
        f"Reported at: {defect.created_at.strftime('%Y-%m-%d %H:%M')}"
    )
    await message.answer(text, parse_mode="HTML")

async def escalate_defect(message: types.Message, command: CommandObject, db_user: Any):
    args = command.args.split()
    if len(args) < 2:
        await message.answer("Usage: /incident escalate {uuid}")
        return
        
    try:
        defect_id = UUID(args[1])
    except ValueError:
        await message.answer("Invalid UUID format.")
        return

    async with AsyncSessionLocal() as db:
        stmt = select(Defect).where(Defect.id == defect_id)
        result = await db.execute(stmt)
        defect = result.scalar_one_or_none()
        
        if not defect:
            await message.answer("Defect not found.")
            return
            
        # Escalation logic: bump severity one level up if possible
        sev_order = ["S4", "S3", "S2", "S1"]
        current_idx = sev_order.index(defect.severity.value)
        if current_idx < len(sev_order) - 1:
            new_sev = sev_order[current_idx + 1]
            defect.severity = DefectSeverity(new_sev)
            defect.status = DefectStatus.TRIAGED # Auto-triage on escalation
            
            from packages.core.domains.defects.models import DefectEvent
            event = DefectEvent(
                defect_id=defect.id,
                event_type="escalated",
                actor_id=db_user.id,
                payload={"new_severity": new_sev}
            )
            db.add(event)
            await db.commit()
            await message.answer(f"🚀 Defect escalated to {new_sev} and status set to triaged.")
        else:
            await message.answer("Defect is already at maximum severity (S1).")

async def get_defect_timeline(message: types.Message, command: CommandObject, db_user: Any):
    args = command.args.split()
    if len(args) < 2:
        await message.answer("Usage: /incident timeline {uuid}")
        return
        
    try:
        defect_id = UUID(args[1])
    except ValueError:
        await message.answer("Invalid UUID format.")
        return

    from packages.core.domains.defects.models import DefectEvent
    async with AsyncSessionLocal() as db:
        stmt = select(DefectEvent).where(DefectEvent.defect_id == defect_id).order_by(DefectEvent.created_at.asc())
        result = await db.execute(stmt)
        events = result.scalars().all()
        
    if not events:
        await message.answer("No timeline events found for this defect.")
        return
        
    text = f"🕒 <b>Timeline for</b> <code>{args[1][:8]}</code>\n\n"
    for e in events:
        text += f"• [{e.created_at.strftime('%H:%M')}] {e.event_type}\n"
        
    await message.answer(text, parse_mode="HTML")
