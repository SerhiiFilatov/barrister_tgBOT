import os
from dotenv import load_dotenv

from aiogram.filters import BaseFilter
from aiogram.types import Message

load_dotenv()

class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == os.getenv('LAWYER_ID')