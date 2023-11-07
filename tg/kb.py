from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
menu = [
    [InlineKeyboardButton(text="💳 Купить LTC", callback_data="buy_ltc")],
    [InlineKeyboardButton(text="💳 Купить BTC", callback_data="buy_btc")],
    [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
    [InlineKeyboardButton(text="💎 Связаться с оператором", callback_data="operator")]
]

operator_menu = [
    [KeyboardButton(text="Посмотреть ")]
]

buy_ltc = [
    [InlineKeyboardButton(text="Подтверждаю", callback_data="confirm_purchase_ltc")],
    [InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase")]
]

buy_btc = [
    [InlineKeyboardButton(text="Подтверждаю", callback_data="confirm_purchase_btc")],
    [InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase")]
]

order = [
    [InlineKeyboardButton(text="Взять", callback_data="take_order")],
]

bought_ltc = [
    [InlineKeyboardButton(text="Оплатил", callback_data="payed")],
    [InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase")]

]
bought_ltc = InlineKeyboardMarkup(inline_keyboard=bought_ltc)


operator_i = [
    [InlineKeyboardButton(text="💲 Изменить курс USD", callback_data="change_usd"),
     InlineKeyboardButton(text="💵 Изменить комиссию", callback_data="change_coms")],
    [InlineKeyboardButton(text="Изменить реквизиты", callback_data="change_cards")],
    [InlineKeyboardButton(text="📝 История заказов", callback_data="order_history")]
]
operator_i = InlineKeyboardMarkup(inline_keyboard=operator_i)


order = InlineKeyboardMarkup(inline_keyboard=order)
buy_btc = InlineKeyboardMarkup(inline_keyboard=buy_btc)
buy_ltc = InlineKeyboardMarkup(inline_keyboard=buy_ltc)
exit_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="◀️ Выйти в меню")]], resize_keyboard=True)
iexit_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Выйти в меню", callback_data="menu")]])
menu = InlineKeyboardMarkup(inline_keyboard=menu)


