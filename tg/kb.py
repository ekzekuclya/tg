from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
menu = [
    [InlineKeyboardButton(text="💳 Купить LTC", callback_data="buy_ltc")],
    [InlineKeyboardButton(text="💳 Купить BTC", callback_data="buy_btc")],
    [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
    [InlineKeyboardButton(text="💎 Связаться с оператором", callback_data="operator")]
]
menu = InlineKeyboardMarkup(inline_keyboard=menu)

exit_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="◀️ Выйти в меню")]], resize_keyboard=True)
iexit_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Выйти в меню", callback_data="menu")]])


buy_ltc = [
    [InlineKeyboardButton(text="Купить", callback_data="confirm_purchase_ltc")],
    [InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase")]
]
buy_ltc = InlineKeyboardMarkup(inline_keyboard=buy_ltc)


buy_btc = [
    [InlineKeyboardButton(text="Купить", callback_data="confirm_purchase_btc")],
    [InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase")]
]

buy_btc = InlineKeyboardMarkup(inline_keyboard=buy_btc)


order = [
    [InlineKeyboardButton(text="Взять", callback_data="take_order")],
      [InlineKeyboardButton(text="Оставить", callback_data="leave_order")]
]
order = InlineKeyboardMarkup(inline_keyboard=order)

