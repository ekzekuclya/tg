from aiogram import Dispatcher, types, Router, Bot, F
from aiogram.filters import Command

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from asgiref.sync import sync_to_async
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import BaseFilter


from . import config, kb, text, chat
from .models import TelegramUser, Order
from .utils import get_ltc_price, get_crypto_price


router = Router()


@router.message(Command("start"))
async def start_handler(msg: Message):
    user_id = msg.from_user.id
    first_name = msg.from_user.first_name
    last_name = msg.from_user.last_name
    username = msg.from_user.username

    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        username=username
    )
    if created:
        print("NEW USER ADDED")
        print(user.first_name, user.username)
    await msg.answer(text.greet.format(name=msg.from_user.full_name), reply_markup=kb.menu)


class BuyCryptoStates(StatesGroup):
    awaiting_crypto_amount = State()


class SendTextState(StatesGroup):
    awaiting_text = State()


class Chat(StatesGroup):
    user = State()
    operator = State()

# @router.message(Command("start"))


@router.callback_query()
async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    if callback_query.data in ["buy_ltc", "buy_btc"]:
        await callback_query.message.delete()
        await callback_query.message.answer(f"Сколько хотите купить?\nНапример: 0.260851", reply_markup=kb.iexit_kb)
        crypto_symbol = callback_query.data[4:]
        await state.update_data(crypto_symbol=crypto_symbol)
        await state.set_state(BuyCryptoStates.awaiting_crypto_amount)



    if callback_query.data == "confirm_purchase_ltc":
        await callback_query.message.answer(f"Отправьте на счёт YOURADMIN OPTIMA: 43255346346345\n"
                                            f"Время ожидания 30 МИНУТ")
    if callback_query.data == "cancel_purchase":
        await callback_query.message.answer("Меню", reply_markup=kb.menu)
    if callback_query.data == "menu":
        await callback_query.message.edit_text(text.greet.format(name=callback_query.from_user.full_name), reply_markup=kb.menu)
    if callback_query.data == "operator":
        await state.set_state(Chat.user)
        user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=callback_query.from_user.id)
        order, _ = await sync_to_async(Order.objects.get_or_create)(user=user, is_active=True)
        operators = await sync_to_async(TelegramUser.objects.filter)(is_admin=True, is_active=True)

        await callback_query.message.answer("Вы связались с оператором. Начните писать вопросы или сообщения.",
                                            reply_markup=kb.exit_kb)
        for operator in operators:
            await bot.send_message(operator.user_id, f"Клиент {callback_query.from_user.username} пишет!\n"
                                                     f"Примите запрос, прежде чем ответить!",
                                   reply_markup=kb.order)

    if callback_query.data == "take_order":
        orders = await sync_to_async(Order.objects.filter)(is_active=True, operator=None)
        order = orders.first()
        operator = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        # print("ORDER OPERATOR TAKE ORDER", order.operator)
        if order and order.operator is None:
            order.operator = operator
            order.save()
            operator.is_active = False
            operator.save()
            await state.set_state(Chat.operator)
            await callback_query.message.edit_text("Вы забрали ордер! \nМожете писать сообщение!")
        if order is None:
            operator.is_active = True
            operator.save()
            await callback_query.message.delete()
            await callback_query.message.answer("Ордер уже забрали")
            await state.clear()


@router.message(Chat.user)
async def user_chat(msg: Message, state: FSMContext, bot: Bot):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=msg.from_user.id)
    order, _ = await sync_to_async(Order.objects.get_or_create)(user=user, is_active=True)
    operators = await sync_to_async(TelegramUser.objects.filter)(is_admin=True, is_active=True)
    print("USER CHAT: ORDER.OPERATOR", order.operator)
    if order.operator is None:
        print("ВНУТРИ ИС НАН")
        for operator in operators:
            print("ВНУТРИ ЦИКЛА ОПЕРАТОРС")
            await msg.forward(operator.user_id)

    if order.operator:
        await msg.forward(order.operator.user_id)

    if msg.text == "EXIT":
        order.is_active = False
        order.operator.is_active = True
        order.save()
        order.operator.save()
        await msg.answer("Вы вышли из чата")
        await state.clear()


@router.message(Chat.operator)
async def chat_operator(message: types.Message, state: FSMContext, bot: Bot):
    operator = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
    order = await sync_to_async(Order.objects.get)(operator=operator, is_active=True)
    print("CHAT OPERATOR", operator.username, order.is_active, order.user, order.operator)
    if order.is_active:
        await bot.send_message(order.user.user_id, message.text, reply_markup=kb.exit_kb)
    else:
        order.is_active = False
        order.save()
        operator.is_active = True
        operator.save()

        await state.clear()


@router.message(BuyCryptoStates.awaiting_crypto_amount)
async def process_crypto_amount(msg: Message, state: FSMContext):
        try:
            data = await state.get_data()
            crypto_symbol = data.get("crypto_symbol")
            crypto_amount = float(msg.text)
            crypto_price = await get_crypto_price(crypto_symbol)
            total_cost = crypto_amount * crypto_price
            await msg.answer(
                f"{crypto_amount} {crypto_symbol.upper()} будет стоить {total_cost} KGS. Желаете подтвердить покупку?",
                reply_markup=kb.buy_btc if crypto_symbol == "btc" else kb.buy_ltc)
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
            await msg.answer(f"{count} {user.username}")
            count += 1
    else:
        await msg.answer("У вас нет прав!")



