import random

from aiogram import Dispatcher, types, Router, Bot, F
from aiogram.filters import Command

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import BaseFilter
from aiogram.utils import markdown as md
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from . import config, kb, text, chat
from .models import TelegramUser, Chat as Order, Exchange, CurrentUsdtCourse, TGMessage
from .utils import get_ltc_price, get_crypto_price, return_bool

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
    if created:
        print("NEW USER ADDED")
        print(user.first_name, user.username)

    if not created:
        user.first_name = msg.from_user.first_name
        user.last_name = msg.from_user.last_name
        user.username = msg.from_user.username
        user.save()

    # if user.is_admin:
    #     await msg.answer(text.greet.format(name=msg.from_user.full_name), reply_markup=)
    await msg.answer(text.greet.format(name=msg.from_user.full_name), reply_markup=kb.menu,
                     parse_mode=ParseMode.MARKDOWN)
    await state.clear()



class BuyCryptoStates(StatesGroup):
    awaiting_crypto_amount = State()


class SendTextState(StatesGroup):
    awaiting_text = State()


class OrderToOperator(StatesGroup):
    awaiting_kvitto = State()


class Chat(StatesGroup):
    user = State()
    operator = State()
    user_id = []


class OperatorAdd(StatesGroup):
    awaiting_user_id = State()

@router.callback_query()
async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    if callback_query.data in ["buy_ltc", "buy_btc"]:
        user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        await callback_query.message.answer(f"Сколько хотите купить?\nНапример: 0.260851", reply_markup=kb.iexit_kb)
        crypto_symbol = callback_query.data[-3:]
        exchange.crypto = crypto_symbol
        print(crypto_symbol)

        exchange.save()
        print(exchange.crypto)
        await state.set_state(BuyCryptoStates.awaiting_crypto_amount)

    if callback_query.data in ["confirm_purchase_ltc", "confirm_purchase_btc"]:

        operators = await sync_to_async(TelegramUser.objects.filter)(is_admin=True)
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        rate = await sync_to_async(CurrentUsdtCourse.objects.first)()
        for operator in operators:
            await bot.send_message(operator.user_id, text.exchange_text.format(exchange_amount=exchange.amount,
                                                                               exchange_crypto=exchange.crypto,
                                                                               exchange_kgs_amount=exchange.kgs_amount +
                                                                               rate.coms,
                                                                               exchange_exchange_rate=
                                                                               exchange.exchange_rate,
                                                                               exchange_created_at=exchange.created_at),
                                   reply_markup=kb.order)
        await callback_query.message.delete()
        await callback_query.message.answer(text=f"Колличество: {exchange.amount}\nВалюта: {exchange.crypto}\nОплата: {exchange.kgs_amount} + комиссия {rate.coms}\nОбщая оплата: {exchange.kgs_amount + rate.coms}\n\nСНИЩУ БУДУТ РЕКВИЗИТЫ",
                                            reply_markup=kb.bought_ltc)

        await state.set_state(Chat.user)

    if callback_query.data == "cancel_purchase":
        await callback_query.message.answer("Меню", reply_markup=kb.menu)
    if callback_query.data == "menu":
        await callback_query.message.edit_text(text.greet.format(name=callback_query.from_user.full_name), reply_markup=kb.menu)
    if callback_query.data == "operator":

        await state.set_state(Chat.user)
        user_info = {
            "user_id": callback_query.from_user.id,
        }
        await state.set_data(user_info)
        orders = await sync_to_async(Order.objects.filter)(is_active=True)

        for order in orders:
            take_order_callback_data = f"take_order_{callback_query.from_user.id}"
            order_i = [[InlineKeyboardButton(text="Взять", callback_data=take_order_callback_data)]]
            order_kb = InlineKeyboardMarkup(inline_keyboard=order_i)
            await bot.send_message(order.operator.user_id, f"Пользователь {callback_query.from_user.full_name} пишет",
                                   reply_markup=order_kb)

        await callback_query.message.answer("Вы связались с оператором. Начните писать вопросы или сообщения.",
                                            reply_markup=kb.exit_kb, one_time_keyboard=False)

    if callback_query.data.startswith("take_order_"):
        operator = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        order, _ = await sync_to_async(Order.objects.get_or_create)(is_active=True, operator=operator)

        user_id = int(callback_query.data.split("_")[2])
        user = await sync_to_async(TelegramUser.objects.get)(user_id=user_id)
        print("CALLBACK USER", user_id)
        is_user_in_chat = return_bool(user)
        if user_id is None:
            await callback_query.message.answer("Ордер уже забрали")
            await state.clear()
        if not is_user_in_chat:
            user = await sync_to_async(TelegramUser.objects.get)(user_id=user_id)
            order.user.add(user)
            order.save()
            await state.set_state(Chat.operator)
            await callback_query.message.edit_text("Вы забрали ордер, можете начать писать!")
        if is_user_in_chat:
            await callback_query.message.answer("Ордер уже забрали")


@router.message(Chat.user)
async def user_chat(msg: Message, state: FSMContext, bot: Bot):
    user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=msg.from_user.id)

    order = await sync_to_async(Order.objects.filter(user=user, is_active=True).first)()

    try:
        tg_message, created = await sync_to_async(TGMessage.objects.get_or_create)(message_id=msg.message_id,
                                                                         sender=user, text=msg.text)
    except IntegrityError:
        print("UNIQ FALSE")
    if order is None:
        operators = await sync_to_async(TelegramUser.objects.filter)(is_admin=True)
        print("ВНУТРИ ИС НАН")
        for operator in operators:
            print("ВНУТРИ ЦИКЛА ОПЕРАТОРС")
            await msg.forward(operator.user_id)


    if msg.text == "EXIT":
        order.user.remove(user)
        # order.save(update_fields=[order.user])
        order.save()
        await msg.answer("Вы вышли из чата")
        await bot.send_message(order.operator.user_id, "Пользователь вышел из чата")
        await state.clear()

    if order is not None:
        tg_message, created = await sync_to_async(TGMessage.objects.get_or_create)(message_id=msg.message_id,
                                                                                   sender=user, text=msg.text)

        tg_message.order = order
        tg_message.save()
        users = order.user.all()
        keyboard = []

        # for user in users:
        #     keyboard.append([KeyboardButton(text=f"{user.username}")])
        #     markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        await msg.forward(order.operator.user_id)


@router.message(Chat.operator)
async def chat_operator(message: types.Message, state: FSMContext, bot: Bot):
    operator = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
    order = await sync_to_async(Order.objects.get)(operator=operator, is_active=True)
    replied_message = message.reply_to_message

    if order.user.count() == 1:
        user = order.user.first()
        await bot.send_message(user.user_id, message.text)

    if replied_message is not None:
        print(replied_message.message_id)
        tg_message = await sync_to_async(TGMessage.objects.get)(message_id=replied_message.message_id-1)
        print(tg_message.text)
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
        await state.set_state(SendTextState.awaiting_text)
    else:
        await msg.answer("У вас нет прав для этой команды")


@router.message(SendTextState.awaiting_text)
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
