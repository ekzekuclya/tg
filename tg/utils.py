import requests
from asgiref.sync import sync_to_async
from .models import Chat


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
            break
    return user_found






