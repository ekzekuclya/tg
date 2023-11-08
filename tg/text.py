from aiogram.utils import markdown as md

greet = ("Здравствуй, *{name}*, добро пожаловать ☺️\n"
         "Мы рады видеть тебя здесь! 🎉\n"
         "Наш бот поможет тебе обменивать криптовалюты без хлопот."
         "Если у тебя возникнут вопросы или нужна помощь, не стесняйся обращаться. 🙋‍♂️\n"
         "Желаем приятных и выгодных сделок! 💰")

menu = "📍 Главное меню"

greet_operator = ("Привет *Operator {name}*!\n"
                  "Ваш админ панель готовится 💰")

exchange_text = ("🤑🤑 Заявка на обмен 🤑🤑\n\n"
                "Количество криптовалюты: {exchange_amount} {exchange_crypto}\n"
                "Сумма в KGS: {exchange_kgs_amount}\n"
                "\nКурс обмена: {exchange_exchange_rate}\n"
                "Дата и время: {exchange_created_at}\n")

start_chat = ("Клиент {name} пишет!\n"
              "Примите запрос, прежде чем ответить!")


exchange_data = (""
                 "")


all_users_admin = "{count} {user_username} ------ HAS ADMIN PERMISSIONS"
all_users = "{count} {user_username}"


order_data = ("Колличество: {amount}\n"
              "Валюта: {crypto}\n"
              "Оплата: {kgs_amount} + комиссия {coms}\n"
              "Общая оплата: {full}"
              "\n\nРеквизиты для оплаты:\n"
              "mBank - {mbank}\n"
              "Optima - {optima}")
