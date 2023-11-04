from aiogram import Bot, Router
from aiogram.enums import ParseMode
from . import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
router = Router()


active_chats = {}


def start_chat(operator_id, user_id):
    active_chats[operator_id] = user_id

# def is_chat_started(operator_id, user_id):
#     return True if active_chats[operator_id] = user_id else False


def end_chat(operator_id):
    if operator_id in active_chats:
        del active_chats[operator_id]


def send_message(sender_id, message):
    recipient_id = None
    for operator_id, user_id in active_chats.items():
        if sender_id == operator_id:
            recipient_id = user_id
        elif sender_id == user_id:
            recipient_id = operator_id

        if recipient_id:
            # Отправка сообщения
            # Например, вы можете использовать бота для отправки сообщения
            bot.send_message(recipient_id, message)
            break
