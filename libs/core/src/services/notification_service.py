from aiogram import Bot
from packages.core.utils.i18n import gettext # Correcting path if needed

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

    async def send_low_stock_notification(
        self, 
        admin_telegram_id: int, 
        locale: str, 
        material_name: str, 
        current_quantity: float, 
        unit: str
    ):
        """
        Notifies the admin that a material has reached or dropped below threshold.
        """
        message = gettext(
            "notification-low-stock",
            locale,
            material=material_name,
            quantity=current_quantity,
            unit=unit
        )
        await self.bot.send_message(admin_telegram_id, message)
