import requests
from aiogram.types import PhotoSize
from asgiref.sync import sync_to_async
from .models import Chat, TelegramUser, Exchange
from datetime import datetime, timedelta
from django.utils import timezone


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
    print(crypto_to_kgs)
    integer = int(crypto_to_kgs)
    print(integer)
    return integer


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
    now = timezone.now()
    cutoff_time = timedelta(minutes=20)
    print(cutoff_time, "CUTOFF_TIME")

    exchanges = await sync_to_async(Exchange.objects.filter)(confirmed=False)

    for exchange in exchanges:
        if exchange.user:
            if exchange.user.last_activity:
                time_inactive = now - exchange.user.last_activity
                if time_inactive > cutoff_time:
                    exchange.operator = None
                    exchange.balance_used = None
                    exchange.save()

    chats = await sync_to_async(Chat.objects.filter)(is_active=True)
    for chat in chats:
        for user in chat.user.all():
            if user.last_activity:
                time_inactive = now - user.last_activity
                if time_inactive >= cutoff_time:
                    print("REMOVED USER", user.username)
                    chat.user.remove(user)
            else:
                print("REMOVED USER", user.username)
                chat.user.remove(user)


async def format_last_activity(last_activity):
    now = timezone.now()
    delta = now - last_activity

    if delta < timedelta(minutes=1):
        return "Только что"
    elif delta < timedelta(hours=1):
        minutes = delta.seconds // 60
        return f"{minutes} {'минут' if minutes % 10 != 1 or minutes == 11 else 'минуту'} назад"
    elif delta < timedelta(days=1):
        hours = delta.seconds // 3600
        return f"{hours} {'часов' if hours % 10 != 1 or hours == 11 else 'час'} назад"
    else:
        days = delta.days
        return f"{days} {'дней' if days % 10 != 1 or days == 11 else 'день'} назад"





