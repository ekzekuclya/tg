from aiogram import Router, F
from aiogram.types import Message

router = Router()


# @router.message(F.new_chat_members)
# async def check_chat_members(msg: Message):
#     print(msg.from_user.username)
#     for user in msg.new_chat_members:
#         print(user.username)
