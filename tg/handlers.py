import random
from datetime import datetime, timedelta

from .states import BuyCryptoStates, SendState, OperatorAdd, Chat, SendStateOperator, PaymentState, UserPayed
from aiogram import types, Router, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from asgiref.sync import sync_to_async
from aiogram.enums.parse_mode import ParseMode
from django.db import IntegrityError
from . import kb, text
from .models import TelegramUser, Chat as Order, Exchange, CurrentUsdtCourse, TGMessage, Payment
from .utils import get_crypto_price, return_bool
import asyncio
router = Router()




@router.message(F.text == "◀️ Выйти в меню")
@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=user_id,
    )
    if user.is_admin:
        await state.set_state(Chat.operator)
        print("ADMIN PANEL")
        order, _ = await sync_to_async(Order.objects.get_or_create)(operator=user)

    if user:
        user.first_name = msg.from_user.first_name
        user.last_name = msg.from_user.last_name
        user.username = msg.from_user.username
        user.save()
        print("user in /start")
        print(user.first_name, user.last_name if user.last_name is not None else '', user.username)

    await msg.answer(text.greet_operator.format(name=msg.from_user.full_name) if user.is_admin
                     else text.greet.format(name=msg.from_user.full_name), reply_markup=kb.operator_i if user.is_admin
                     else kb.menu, parse_mode=ParseMode.MARKDOWN)
    await state.clear()


@router.callback_query()
async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    if callback_query.data in ["buy_ltc", "buy_btc"]:
        user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        await callback_query.message.answer(f"Сколько хотите купить?\nНапример: 0.260851", reply_markup=kb.iexit_kb)
        crypto_symbol = callback_query.data[-3:]
        exchange.crypto = crypto_symbol
        exchange.save()
        await state.set_state(BuyCryptoStates.awaiting_crypto_amount)

    if callback_query.data in ["confirm_purchase_ltc", "confirm_purchase_btc"]:

        operators = await sync_to_async(TelegramUser.objects.filter)(is_admin=True)
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        exchange.operator = None
        exchange.save()
        rate = await sync_to_async(CurrentUsdtCourse.objects.first)()
        # payment = await sync_to_async(Payment.objects.first)()
        payments = await sync_to_async(Payment.objects.all)()
        payment = random.choice(payments)
        exchange.operator = payment.operator
        exchange.save()
        await callback_query.message.delete()
        await callback_query.message.answer(text=text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                            kgs_amount=exchange.kgs_amount, coms=rate.coms, full=exchange.kgs_amount +
                                            rate.coms, mbank=payment.mbank, optima=payment.optima),
                                            reply_markup=kb.bought_ltc)

    if callback_query.data == "order_operator":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        rate = await sync_to_async(CurrentUsdtCourse.objects.first)()
        orders = await sync_to_async(Order.objects.filter)(is_active=True)
        for order in orders:
            if user in order.user.all():
                order.user.remove(user)
                order.save()
        if exchange.operator:
            orders = await sync_to_async(Order.objects.filter)(operator=exchange.operator, is_active=True)
            order = orders.first()
            order.user.add(user)
            take_order_callback_data = f"take_order_{callback_query.from_user.id}"
            order_i = [[InlineKeyboardButton(text="Взять", callback_data=take_order_callback_data)]]
            order_kb = InlineKeyboardMarkup(inline_keyboard=order_i)
            await bot.send_message(exchange.operator.user_id, text.exchange_text.format(exchange_amount=exchange.amount,
                                                                                     exchange_crypto=exchange.crypto,
                                                                                     exchange_kgs_amount=exchange.kgs_amount + rate.coms,
                                                                                     exchange_exchange_rate=exchange.exchange_rate,
                                                                                     exchange_created_at=exchange.created_at),
                                   reply_markup=order_kb)
            await state.set_state(Chat.user)
            await callback_query.message.answer("Вы связались с оператором. Начните писать вопросы или сообщения.",
                                                one_time_keyboard=False)
        # if not exchange.operator:
        #     for order in orders:
        #         if user in order.user.all():
        #             order.user.remove(user)
        #         take_order_callback_data = f"take_order_{callback_query.from_user.id}"
        #         order_i = [[InlineKeyboardButton(text="Взять", callback_data=take_order_callback_data)]]
        #         order_kb = InlineKeyboardMarkup(inline_keyboard=order_i)
        #         await bot.send_message(order.operator.user_id, text.exchange_text.format(exchange_amount=exchange.amount,
        #                                exchange_crypto=exchange.crypto, exchange_kgs_amount=exchange.kgs_amount + rate.coms,
        #                                exchange_exchange_rate=exchange.exchange_rate,exchange_created_at=exchange.created_at),
        #                                reply_markup=order_kb)
        #     await state.set_state(Chat.user)

        # await asyncio.sleep(5)
        # await callback_query.message.answer("Приветствую, чем я могу вам помочь")
    if callback_query.data == "cancel_purchase":
        await callback_query.message.answer("Меню", reply_markup=kb.menu)
    if callback_query.data == "menu":
        await callback_query.message.edit_text(text.greet.format(name=callback_query.from_user.full_name), reply_markup=kb.menu)
    if callback_query.data == "operator":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        await state.set_state(Chat.user)

        orders = await sync_to_async(Order.objects.filter)(is_active=True)

        for order in orders:
            if user in order.user.all():
                order.user.remove(user)
            take_order_callback_data = f"take_order_{callback_query.from_user.id}"
            order_i = [[InlineKeyboardButton(text="Взять", callback_data=take_order_callback_data)]]
            order_kb = InlineKeyboardMarkup(inline_keyboard=order_i)
            await bot.send_message(order.operator.user_id, f"Пользователь {callback_query.from_user.full_name} пишет",
                                   reply_markup=order_kb)

        await callback_query.message.answer("Вы связались с оператором. Начните писать вопросы или сообщения.",
                                            reply_markup=ReplyKeyboardRemove())    # one_time_keyboard=False

    if callback_query.data.startswith("take_order_"):
        operator = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        order, _ = await sync_to_async(Order.objects.get_or_create)(is_active=True, operator=operator)

        user_id = int(callback_query.data.split("_")[2])
        user = await sync_to_async(TelegramUser.objects.get)(user_id=user_id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user)

        if exchange.operator == operator:
            order.user.add(user)
            order.save()
            await state.set_state(Chat.operator)
            await callback_query.message.answer("✔ Вы забрали ордер, можете начать писать!", reply_markup=kb.send_order,
                                                one_time_keyboard=False)
        else:
            await callback_query.message.answer("Забрали")
    if callback_query.data == "payed":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        await state.set_state(UserPayed.awaiting_photo)
        await callback_query.message.answer("Пожалуйста отправьте фото чека")
        await callback_query.message.forward(exchange.operator.user_id)
        await bot.send_message(exchange.operator.user_id, "Подтвердите получение денег")

    if callback_query.data in ["change_usdt", "change_coms", "change_card"]:
        data = callback_query.data[-4:]
        course = await sync_to_async(CurrentUsdtCourse.objects.first)()
        await state.clear()

        if data == "usdt":
            await callback_query.message.answer(f"Нынешний курс USDT - 💲{course.usdt}\nВведите желаемые курс")
            await state.set_state(SendStateOperator.awaiting_usdt)
        elif data == "coms":
            await callback_query.message.answer(f"Стоимость комиссии - 💵{course.coms} сом\nВведите желаемые курс")
            await state.set_state(SendStateOperator.awaiting_coms)
        elif data == "card":
            await callback_query.message.answer(f"Как реквизит хочешь изменить?", reply_markup=kb.card)

    if callback_query.data in ["change_mbank", "change_optima"]:
        data = callback_query.data
        await state.clear()
        if data == "change_optima":
            await callback_query.message.edit_text("💶 Введите новый реквизит для Optima")
            await state.set_state(PaymentState.awaiting_optima)
        elif data == "change_mbank":
            await callback_query.message.answer("💴 Введите новый реквизит для mBank")
            await state.set_state(PaymentState.awaiting_mbank)


@router.message(Chat.user)
async def user_chat(msg: Message, state: FSMContext, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    exchange, created = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
    tg_message, created = await sync_to_async(TGMessage.objects.get_or_create)(message_id=msg.message_id, sender=user)
    photo = msg.photo
    if exchange.operator:
        order = await sync_to_async(Order.objects.get)(operator=exchange.operator, is_active=True)
        order.user.add(user)
        order.save()
        tg_message.order = order
        tg_message.save()
        await msg.forward(exchange.operator.user_id, photo=photo if photo else None)
        print("IF USER IN CHAT")

    user.last_activity = datetime.now()
    user.save()
    orders = await sync_to_async(Order.objects.filter)(is_active=True)
    user_in_chat = await return_bool(user)

    if not user_in_chat:
        for i in orders:
            await msg.forward(i.operator.user_id)


@router.message(Chat.operator)
async def chat_operator(message: types.Message, state: FSMContext, bot: Bot):
    operator = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
    order = await sync_to_async(Order.objects.get)(operator=operator, is_active=True)
    replied_message = message.reply_to_message

    if message.text.startswith("◀️ Отп"):       # Отправить
        print()
        users = order.user.all()
        users = users.order_by('-last_activity')
        newest_user = users.first()
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=newest_user, confirmed=False)
        rate = await sync_to_async(CurrentUsdtCourse.objects.first)()
        payment = await sync_to_async(Payment.objects.get)(operator=operator)
        await bot.send_message(chat_id=newest_user.user_id,text=text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                             kgs_amount=exchange.kgs_amount, coms=rate.coms, full=exchange.kgs_amount + rate.coms,
                             mbank=payment.mbank, optima=payment.optima),
                             reply_markup=kb.bought_ltc_operator)
        await message.answer(text="ВЫ ОТПРАВИЛИ ЕМУ ОРДЕР:\n" + text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                             kgs_amount=exchange.kgs_amount, coms=rate.coms, full=exchange.kgs_amount + rate.coms,
                             mbank=payment.mbank, optima=payment.optima))

    elif order.user.count() == 1:
        user = order.user.first()
        await bot.send_message(user.user_id, message.text)

    elif order.user.count() > 1 and replied_message is None:
        users = order.user.all()
        users = users.order_by('-last_activity')
        newest_user = users.first()
        await bot.send_message(newest_user.user_id, message.text)
    elif replied_message is not None:
        tg_message = await sync_to_async(TGMessage.objects.get)(message_id=replied_message.message_id - 1)
        order.user.add(tg_message.sender)
        order.save()
        await bot.send_message(tg_message.sender.user_id, message.text)


@router.message(BuyCryptoStates.awaiting_crypto_amount)
async def process_crypto_amount(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        usdt = await sync_to_async(CurrentUsdtCourse.objects.first)()
        crypto_amount = float(msg.text)
        print(exchange.crypto)
        crypto_price = await get_crypto_price(str(exchange.crypto), usdt.usdt)
        total_cost = crypto_amount * crypto_price
        exchange.amount = crypto_amount
        exchange.kgs_amount = total_cost
        exchange.exchange_rate = crypto_price
        exchange.save()
        await msg.answer(
            f"{crypto_amount} {exchange.crypto.upper()} будет стоить {total_cost} KGS. Желаете подтвердить покупку?",
            reply_markup=kb.buy_btc if exchange.crypto == "btc" else kb.buy_ltc)
        await state.clear()

    except ValueError:
        await msg.answer("Пожалуйста, введите корректное количество криптовалюты (число).")


@router.message(Command("send"))
async def send_command(msg: Message, state: FSMContext):
    user_id = msg.from_user.id
    username = msg.from_user.username

    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=user_id,
        username=username
    )
    if user.is_admin:
        await msg.answer("Введите текст, который вы хотите отправить всем пользователям.")
        await state.set_state(SendState.awaiting_text)
    else:
        await msg.answer("У вас нет прав для этой команды")


@router.message(SendState.awaiting_text)
async def handle_send_all(message: types.Message, state: FSMContext, bot: Bot):
    text_to_send = message.text

    users = await sync_to_async(TelegramUser.objects.all)()

    for user in users:
        try:
            chat_member = await bot.get_chat_member(user.user_id, user.user_id)
            if chat_member.status != "left" and chat_member.status != "kicked":
                # Пользователь не заблокировал бота, отправляем сообщение
                await bot.send_message(user.user_id, text_to_send)
                await message.answer(f"Сообщение отправлено пользователю: {user.username}")
            else:
                await message.answer(f"Сообщение НЕ отправлено: {user.username}")
                print(f"Пользователь {user.username} заблокировал бота")
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user.username}: {str(e)}")

    await message.answer(f"Вы отправили сообщение:\n\n{text_to_send}\n\nвсем пользователям в боте.")
    await state.clear()


@router.message(Command("users"))
async def send_users(msg: Message):
    user_id = msg.from_user.id
    username = msg.from_user.username

    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=user_id,
        username=username
    )
    if user.is_admin:
        users = await sync_to_async(TelegramUser.objects.all)()
        count = 1
        for user in users:
            if user.is_admin:
                await msg.answer(text=f"{count} {user.username} ------ HAS ADMIN PERMISSIONS", parse_mode=None)
                count += 1
            else:
                await msg.answer(text=f"{count} {user.username}", parse_mode=None)
                count += 1
    else:
        await msg.answer("У вас нет прав!")


@router.message(Command("permission"))
async def add_permission(msg: Message, state: FSMContext):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=msg.from_user.id,
    )
    await state.set_state(OperatorAdd.awaiting_user_id)


@router.message(OperatorAdd.awaiting_user_id)
async def awaiting_user_id(msg: Message, state: FSMContext):
    try:
        user_id = msg.text
        user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=user_id)
        user.is_admin = True
        user.save()
        await msg.answer("Пользователь добавлен в операторы")
        await state.clear()
    except Exception:
        await msg.answer("Произошла ошибка")


@router.message(SendState.awaiting_kvitto)
async def awaiting_kvitto(msg: Message, state: FSMContext):
    print(msg.photo)
    if msg.photo:
        await msg.forward(msg.from_user.id, photo=msg.photo)


@router.message(SendStateOperator.awaiting_coms)
@router.message(SendStateOperator.awaiting_usdt)
async def awaiting_usdt(msg: Message, state: FSMContext):
    try:
        current_state = await state.get_state()
        course = await sync_to_async(CurrentUsdtCourse.objects.first)()
        if current_state == 'SendStateOperator:awaiting_usdt':
            print("IN CURRENT STATE", current_state)
            new_usdt = float(msg.text)
            course.usdt = new_usdt
            course.save()
            await msg.answer(f"Курс изменён на {new_usdt}")
            await state.clear()
        elif current_state == 'SendStateOperator:awaiting_coms':
            new_coms = int(msg.text)
            course.coms = new_coms
            course.save()
            await msg.answer(f"Комиссия изменена на {new_coms}")
            await state.clear()

    except Exception:
        await msg.answer("Введите верный формат, введите число, например 91")


@router.message(PaymentState.awaiting_optima)
@router.message(PaymentState.awaiting_mbank)
async def awaiting_card(msg: Message, state: FSMContext):
    try:
        current_state = await state.get_state()
        operator = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        payment, _ = await sync_to_async(Payment.objects.get_or_create)(operator=operator)
        if current_state == 'PaymentState:awaiting_mbank':
            new_mbank = msg.text
            payment.mbank = new_mbank
            payment.save()
            await msg.answer(f"Курс изменён на {new_mbank}")
            await state.clear()
        elif current_state == 'PaymentState:awaiting_optima':
            new_optima = str(msg.text)
            payment.optima = new_optima
            payment.save()
            await msg.answer(f"Реквизиты Optima изменены на {new_optima}", reply_markup=kb.card)
            await state.clear()
    except Exception as e:
        print(e)
        await msg.answer("Введите верный формат, введите числа!")


# @router.message(UserPayed.awaiting_photo)
# async def awaiting_payed_photo(msg: Message, state: FSMContext):
#     photo = msg.photo
#
#     if photo:

