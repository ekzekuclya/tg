import requests


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
