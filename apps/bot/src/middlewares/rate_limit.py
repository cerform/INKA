from typing import Any, Awaitable, Callable, Dict
import time
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from packages.core.config import settings

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 1.0):
        self.limit = limit
        self.last_calls = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.time()
        
        if user_id in self.last_calls:
            delta = now - self.last_calls[user_id]
            if delta < self.limit:
                # Silently ignore or send a warning
                return

        self.last_calls[user_id] = now
        return await handler(event, data)
