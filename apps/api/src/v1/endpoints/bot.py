from fastapi import APIRouter, types, Request
from aiogram import types as tg_types
from apps.bot.main import bot, dp
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def bot_webhook(request: Request):
    update = tg_types.Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
