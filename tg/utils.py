import requests
from aiogram.types import PhotoSize
from asgiref.sync import sync_to_async
from .models import Chat, TelegramUser, Exchange
from datetime import datetime, timedelta

from pytz import timezone  # Импортируйте pytz


def get_ltc_price():
    url = "https://openexchangerates.org/api/latest.json?app_id=84c6243309e84299a2b028f8c55d21d8"
    response = requests.get(url)
    data = response.json()

    usd_to_kgs = data['rates']['KGS']

    url = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    ltc_to_usd = data['litecoin']['usd']

    ltc_to_kgs = ltc_to_usd * usd_to_kgs
    return ltc_to_kgs


async def get_crypto_price(crypto_symbol, usdt):
    if crypto_symbol == "ltc":
        crypto_key = "litecoin"
    elif crypto_symbol == "btc":
        crypto_key = "bitcoin"
    else:
        raise ValueError("Invalid cryptocurrency symbol")

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_key}&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()

    crypto_to_usd = data[crypto_key]['usd']
    crypto_to_kgs = crypto_to_usd * usdt
    return crypto_to_kgs


async def return_bool(user):
    chats = await sync_to_async(Chat.objects.filter)(is_active=True)
    user_found = False
    for chat in chats:
        if user in chat.user.all():
            user_found = True
            return user_found, chat.operator
    return user_found, None


async def check_inactive_users():
    print("IM IN INACTIVE USERS")
    utc = timezone('UTC')
    now = utc.localize(datetime.now())
    cutoff_time = timedelta(minutes=15)

    exchanges = await sync_to_async(Exchange.objects.filter)(confirmed=False)

    for exchange in exchanges:
        if exchange.user.last_activity:
            time_inactive = now - exchange.user.last_activity
            if time_inactive > cutoff_time:
                exchange.operator = None
                exchange.save()

    chats = await sync_to_async(Chat.objects.filter)(is_active=True)
    for chat in chats:
        for user in chat.user.all():
            if user.last_activity:
                time_inactive = now - user.last_activity
                if time_inactive > cutoff_time:
                    print("REMOVED USER", user.username)
                    chat.user.remove(user)
            else:
                print("REMOVED USER", user.username)
                chat.user.remove(user)



photo = [PhotoSize(file_id='AgACAgIAAxkBAAIFV2VKv6orCN0L8QSybezlpx0rxrVzAAL10TEbpGJYSg4ihKLAZ06FAQADAgADcwADMwQ',
                   file_unique_id='AQAD9dExG6RiWEp4', width=90, height=90, file_size=1482),
         PhotoSize(file_id='AgACAgIAAxkBAAIFV2VKv6orCN0L8QSybezlpx0rxrVzAAL10TEbpGJYSg4ihKLAZ06FAQADAgADbQADMwQ',
                   file_unique_id='AQAD9dExG6RiWEpy', width=320, height=320, file_size=24028),
         PhotoSize(file_id='AgACAgIAAxkBAAIFV2VKv6orCN0L8QSybezlpx0rxrVzAAL10TEbpGJYSg4ihKLAZ06FAQADAgADeAADMwQ',
                   file_unique_id='AQAD9dExG6RiWEp9', width=736, height=736, file_size=86045)]


