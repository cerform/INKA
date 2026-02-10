import uuid
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        request_id = str(uuid.uuid4())
        actor_id = None
        
        user = data.get("event_from_user")
        if user:
            actor_id = str(user.id)

        # We can use a ContextVar or just pass it in the data
        data["log_context"] = {"request_id": request_id, "actor_id": actor_id}
        
        # Unfortunately, standard logging doesn't easily pick up from data dict
        # without custom adapters or filters that look at a context var.
        # But for now, we'll manually inject if needed or use a filter.
        return await handler(event, data)
