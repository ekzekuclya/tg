from aiogram.utils import markdown as md

greet = ("Приветствую *@{name}* 🤜🤛\n\n"
         "Я 🤖 бот обменник! \n"
         "Здесь вы можете обменять свои *KGS* на *LTC/BTC*\n\n"
         "Если у тебя возникнут вопросы или нужна помощь обращайтесь по кнопки ниже 👇\n\n"
         "Выбирай *валюту* ⚡️ или ознакомься с *балансом* 💰")


# Отправка сообщения с HTML-форматированием


menu = "📍 Главное меню"

greet_operator = ("Привет *Operator {name}*!\n"
                  "Ваш админ панель готовится 💰")

exchange_text = ("➡➖➖➖ *Зявка* ➖➖➖➖\n"
              "⚡️*{crypto}*⚡️ 🟰 `{amount}` \n"
              "💸 *Стоимость* 🟰 `{kgs_amount}` _сом_ \n"
              "💴 *Комиссия* 🟰 `{coms}` _сом_ \n\n"
              "💰 *Сумма* 🟰 `{full}` _сом_")

start_chat = ("Клиент {name} пишет!\n"
              "Примите запрос, прежде чем ответить!")




all_users_admin = "{count} {user_username} ------ HAS ADMIN PERMISSIONS"
all_users = "{count} {user_username}"


"""
➖➖➖➖ORDER➖➖➖➖
⚡️LTC⚡️ 🟰 1.0
💸 Стоимость 🟰 7456 сом
💴 Комиссия 🟰 100сом

💰 К оплате 🟰 7556 сом
"""


order_data = ("➡➖➖➖ *ORDER* ➖➖➖➖\n"
              "⚡️*{crypto}*⚡️ 🟰 `{amount}` \n"
              "💸 *Стоимость* 🟰 `{kgs_amount}` _сом_ \n"
              "💴 *Комиссия* 🟰 `{coms}` _сом_ \n\n"
              "💰 *Сумма* 🟰 `{full}` _сом_")

order_payments = ("\n\n➖➖➖➖*PAYMENT*➖➖➖➖\n\n"
              "💳 *MBANK* 🟰 `{mbank}`\n"
              "💳 *OPTIMA* 🟰 `{optima}`\n")


order_data_short = ("Колличество: {amount}\n Валюта: {crypto}\n Оплата: {kgs_amount} + комиссия {coms}\n Общая оплата: "
                    "{full}\n\n")

