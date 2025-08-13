import os
from dotenv import load_dotenv

from aiogram.filters import BaseFilter
from aiogram.types import Message

load_dotenv()

class AdminFilter(BaseFilter):
    def __init__(self):
        self.admin_id = int(os.getenv('LAWYER_ID'))

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == self.admin_id