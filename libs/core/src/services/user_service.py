from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from packages.core.models.user import User

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.telegram_id == telegram_id, User.is_active == True)
        )
        return result.scalars().first()

    async def get_user_locale(self, telegram_id: int) -> str:
        user = await self.get_by_telegram_id(telegram_id)
        return user.language_code if user else "en"
