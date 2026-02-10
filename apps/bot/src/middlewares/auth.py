from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject
from packages.core.services.user_service import UserService
from packages.db.session import AsyncSessionLocal

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user: types.User = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        async with AsyncSessionLocal() as session:
            user_service = UserService(session)
            db_user = await user_service.get_by_telegram_id(user.id)
            
            if not db_user:
                if isinstance(event, types.Message):
                    await event.answer("⚠️ Access denied. You are not on the allowlist.")
                return 

            data["db_user"] = db_user
            return await handler(event, data)

class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        db_user = data.get("db_user")
        locale = db_user.language_code if db_user else "en"
        data["locale"] = locale
        return await handler(event, data)
