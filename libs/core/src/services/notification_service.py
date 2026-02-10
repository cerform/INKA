from aiogram import Bot
from apps.bot.utils.i18n import gettext

class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_booking_reminder(self, telegram_id: int, locale: str, booking_details: dict):
        message = gettext(
            "notification-reminder",
            locale,
            time=booking_details["time"],
            master=booking_details["master"],
            service=booking_details["service"]
        )
        await self.bot.send_message(telegram_id, message)

    async def notify_admin_new_booking(self, admin_telegram_id: int, locale: str, booking_details: dict):
        message = gettext(
            "notification-new-booking",
            locale,
            client=booking_details["client"],
            time=booking_details["time"]
        )
        await self.bot.send_message(admin_telegram_id, message)
