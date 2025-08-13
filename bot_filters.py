from config import settings
from aiogram.filters import BaseFilter
from aiogram.types import Message


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == settings.admin_id