import random
from datetime import datetime, timedelta

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from .config import CHANNEL_ID
from .states import BuyCryptoStates, SendState, OperatorAdd, Chat, SendStateOperator, PaymentState, UserPayed, \
    PromoCodeAdmin, PromoCodeUser
from aiogram import types, Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from asgiref.sync import sync_to_async
from aiogram.enums.parse_mode import ParseMode
from django.db import IntegrityError
from . import kb, text
from .models import TelegramUser, Chat as Order, Exchange, CurrentUsdtCourse, TGMessage, Payment, Promo
from .utils import get_crypto_price, return_bool, format_last_activity
import asyncio
router = Router()
from django.utils import timezone


@router.message(F.text == "◀️ Выйти в меню")
@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext, command: CommandObject, bot: Bot):
    user_id = msg.from_user.id
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=user_id,
    )
    is_subscribed = await bot.get_chat_member(chat_id="@BestChangeKgz", user_id=msg.from_user.id)
    referred_by_id = command.args
    if is_subscribed.status in ['member', 'administrator', 'creator']:
        if created:
            user.first_name = msg.from_user.first_name
            user.last_name = msg.from_user.last_name
            user.username = msg.from_user.username
            user.save()
            if user.referred_by is None and referred_by_id:
                referred_user = await sync_to_async(TelegramUser.objects.get)(id=referred_by_id)
                user.referred_by = referred_user
                user.save()
                await bot.send_message(referred_user.user_id, f"🎈 Пользователь @{user.username} зарегистрировался под "
                                                              f"вашей ссылкой! \nВы просто великолепны! 💚", parse_mode=None)
            print(referred_by_id)
        if user.is_admin:

            await state.set_state(Chat.operator)
            print("ADMIN PANEL")
            order, _ = await sync_to_async(Order.objects.get_or_create)(operator=user)

        if user:
            user.first_name = msg.from_user.first_name
            user.last_name = msg.from_user.last_name
            user.username = msg.from_user.username
            user.last_activity = timezone.now()
            user.save()
            print("user in /start")
            print(user.first_name, user.last_name if user.last_name is not None else '', user.username)
        try:
            photo_id = "AgACAgIAAxkBAAIVdWVQJD5HZcULlEVlPM9oYAENoY1_AAKb0jEbZJCASsd3CKpCrSO4AQADAgADcwADMwQ"
            await bot.send_photo(chat_id=msg.from_user.id, photo=photo_id)

        except Exception as e:
            print("PHOTO DID NOT SENT")
        await msg.answer(text.greet_operator.format(name=msg.from_user.username) if user.is_admin
                         else text.greet.format(name=msg.from_user.username if msg.from_user.username else msg.from_user.full_name),
                         reply_markup=kb.operator_i if user.is_admin
                         else kb.menu, parse_mode=ParseMode.MARKDOWN)
        await state.clear()
    else:
        await msg.answer("Подпишитесь на канал", reply_markup=kb.not_subscribed)


@router.callback_query()
async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    if callback_query.data == "check_subs":
        is_subscribed = await bot.get_chat_member(chat_id="@BestChangeKgz", user_id=callback_query.from_user.id)
        if is_subscribed.status in ['member', 'administrator', 'creator']:
            await callback_query.message.edit_text("Вы подписаны, можете пользоваться", reply_markup=kb.menu)

    if callback_query.data in ["buy_ltc", "buy_btc"]:
        user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        crypto_symbol = callback_query.data[-3:]
        exchange.crypto = crypto_symbol
        exchange.save()
        print(exchange.operator)
        buy_ltc_text = "*Введите желаемое колличество* ⚡️*{}*⚡️\n\n_Например_ `0.21468`".format(crypto_symbol.upper())
        await callback_query.message.answer(buy_ltc_text, reply_markup=kb.iexit_kb)

        await state.set_state(BuyCryptoStates.awaiting_crypto_amount)
        await callback_query.answer(f"Введите {crypto_symbol}")
        if exchange.operator:

            print("EXCHANGE.OPERATOR", exchange.operator.user_id, exchange.operator.username, exchange.operator)
            await state.update_data(operator_id=exchange.operator.user_id)
            await bot.send_message(chat_id=exchange.operator.user_id, text="Пользователь {} набирает кол-во {}".format
            (user.username, crypto_symbol), parse_mode=None)

    if callback_query.data.startswith("confirm_purchase_"):  #in ["confirm_purchase_ltc", "confirm_purchase_btc"]:
        payment_id = callback_query.data[20:]
        payment = await sync_to_async(Payment.objects.get)(id=payment_id)
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)

        exchange.operator = payment.operator
        exchange.save()

        if exchange.balance_used is not None:
            response_text = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto.upper(),
                                                   kgs_amount=exchange.kgs_amount,
                                                   coms=payment.coms, full=exchange.kgs_amount + payment.coms - user.balance)
            response_text += f"\n🚩 *Использован баланс* `{user.balance}`_с_"
            response_text += text.order_payments.format(mbank=payment.mbank, optima=payment.optima)
            await callback_query.message.delete()
            await callback_query.message.answer(text=response_text, reply_markup=kb.bought_ltc)
            return
        response_text = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                               kgs_amount=exchange.kgs_amount,
                                               coms=payment.coms, full=exchange.kgs_amount + payment.coms)
        response_text += text.order_payments.format(mbank=payment.mbank, optima=payment.optima)
        await callback_query.message.delete()
        await callback_query.message.answer(text=response_text, reply_markup=kb.bought_ltc)

    if callback_query.data == "order_operator":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)
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
            print(exchange.user, exchange.id)
            print("EXCHANGE CRYPTO", exchange.crypto)

            response_text = text.exchange_text.format(amount=exchange.amount, crypto=exchange.crypto.upper(),
                                                kgs_amount=int(exchange.kgs_amount), coms=payment.coms,
                                                full=int(exchange.kgs_amount + payment.coms))
            if exchange.balance_used is not None:
                response_text = text.exchange_text.format(amount=exchange.amount, crypto=exchange.crypto.upper(),
                                                kgs_amount=int(exchange.kgs_amount), coms=payment.coms,
                                                full=int(exchange.kgs_amount + payment.coms - user.balance))
                response_text += f"\n🚩 *Использован баланс* `{user.balance}`_с_"
                await bot.send_message(exchange.operator.user_id, response_text, reply_markup=order_kb)
                await state.set_state(Chat.user)
                await callback_query.message.answer("Вы связались с оператором. Начните писать вопросы или сообщения.",
                                                    one_time_keyboard=False)
                return
            await bot.send_message(exchange.operator.user_id, response_text, reply_markup=order_kb)
            await state.set_state(Chat.user)
            await callback_query.message.answer("Вы связались с оператором. Начните писать вопросы или сообщения.",
                                                one_time_keyboard=False)

    if callback_query.data == "cancel_purchase":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        await callback_query.message.edit_text(text.greet_operator.format(name=callback_query.from_user.username) if user.is_admin
                         else text.greet.format(name=callback_query.from_user.full_name),
                         reply_markup=kb.operator_i if user.is_admin
                         else kb.menu, parse_mode=ParseMode.MARKDOWN)
    if callback_query.data == "cencel_purchase_operator":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        await callback_query.message.edit_text(
            text.greet_operator.format(name=callback_query.from_user.username) if user.is_admin
            else text.greet.format(name=callback_query.from_user.full_name),
            reply_markup=kb.operator_i if user.is_admin
            else kb.menu, parse_mode=ParseMode.MARKDOWN)
    if callback_query.data == "menu":
        await callback_query.message.delete()
        # await callback_query.message.edit_text(text.greet.format(name=callback_query.from_user.full_name), reply_markup=kb.menu)
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
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        user_in_chat, chat_operator = await return_bool(user)
        if exchange.operator == operator:
            order.user.add(user)
            order.save()
            await state.set_state(Chat.operator)
            await callback_query.message.answer("✔ Вы забрали ордер, можете начать писать!", reply_markup=kb.send_order,
                                                one_time_keyboard=False)
        if not user_in_chat:
            order.user.add(user)
            order.save()
            await state.set_state(Chat.operator)
            await callback_query.message.answer("✔ Вы забрали ордер, можете начать писать!", reply_markup=kb.send_order,
                                                one_time_keyboard=False)
        if user_in_chat:
            exchange.operator = chat_operator
            exchange.save()
            await callback_query.message.answer(f"Ордер забрал оператор {chat_operator.username}")

    if callback_query.data == "payed":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)
        awaiting_kvitto = text.order_data.format(
                amount=exchange.amount, crypto=exchange.crypto, kgs_amount=exchange.kgs_amount, coms=
                payment.coms, full=exchange.kgs_amount + payment.coms)
        keyboard = InlineKeyboardBuilder()
        await callback_query.message.answer("Пожалуйста отправьте фото чека")
        if exchange.balance_used is not None:
            awaiting_kvitto += text.order_data.format(
                amount=exchange.amount, crypto=exchange.crypto, kgs_amount=exchange.kgs_amount, coms=
                payment.coms, full=exchange.kgs_amount + payment.coms - exchange.balance_used)
            awaiting_kvitto += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used}"
            awaiting_kvitto += f"\n\n 🟡 @{user.username if user.username else callback_query.from_user.full_name} отметил *Оплатил*"
            await bot.send_message(exchange.operator.user_id, text=awaiting_kvitto, reply_markup=keyboard.as_markup())
            await state.set_state(UserPayed.awaiting_photo)
            return
        awaiting_kvitto += text.order_payments.format(mbank=payment.mbank,
                                                     optima=payment.optima)
        awaiting_kvitto += "\n\n✅✅☑️ *ПОДТВЕРЖДЕНИЕ*"
        await callback_query.message.edit_text(awaiting_kvitto)
        awaiting_kvitto += f"\n\n 🟡 @{user.username if user.username else callback_query.from_user.full_name} отметил *Оплатил*"
        await bot.send_message(exchange.operator.user_id, text=awaiting_kvitto, reply_markup= keyboard.as_markup())
        await state.set_state(UserPayed.awaiting_photo)


        # await bot.send_message(exchange.operator.user_id, f"Пользователь {user.username} нажал что оплатил", reply_markup=)

    if callback_query.data in ["change_usdt", "change_coms", "change_card"]:
        data = callback_query.data[-4:]
        operator = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        payment, _ = await sync_to_async(Payment.objects.get_or_create)(operator=operator)
        await state.clear()

        if data == "usdt":
            await callback_query.message.answer(f"Нынешний курс Ваш USDT - 💲{payment.usdt}\nВведите желаемые курс")
            await state.set_state(SendStateOperator.awaiting_usdt)
        elif data == "coms":
            await callback_query.message.answer(f"Стоимость комиссии - 💵{payment.coms} сом\nВведите желаемые курс")
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

    if callback_query.data.startswith("next_page_"):
        page = int(callback_query.data.split("_")[2])
        print("NEXT PAGE", page + 1)
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        await get_reviews_page(callback_query.message, page + 1, user)
    if callback_query.data.startswith("prev_page_"):
        page = int(callback_query.data.split("_")[2])
        print("PREV PAGE", page - 1)
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        await get_reviews_page(callback_query.message, page - 1, user)

    if callback_query.data.startswith("confirm_payed_kgs"):
        validate = callback_query.data[14:18]
        exchange_id = callback_query.data[18:]
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        print("VALIDATE", validate)
        print(callback_query.data)
        print(exchange_id)
        if validate == "kgs1":
            if user.is_admin:
                exchange = await sync_to_async(Exchange.objects.get)(id=exchange_id)
                payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)
                keyboard = InlineKeyboardBuilder()
                validate_text = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                       kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                       full=int(exchange.kgs_amount + payment.coms))
                keyboard.add(InlineKeyboardButton(text="ДА!", callback_data=f"confirm_payed_kgs2{exchange.id}"))
                keyboard.add(InlineKeyboardButton(text="Написать", callback_data=f"take_order_{exchange.user.user_id}"))
                if exchange.balance_used is not None:
                    validate_text = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                           kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                           full=int(exchange.kgs_amount + payment.coms - user.balance))
                    validate_text += f"\n🚩 *Использован баланс* `{user.balance}`_с_"
                validate_text += "\n\n✅✅☑️ *Подтвердите*"
                await callback_query.message.edit_text(text= validate_text, reply_markup=keyboard.as_markup())
                operator = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
                order = await sync_to_async(Order.objects.get)(operator=operator)
                order.user.add(exchange.user)
                await state.set_state(Chat.operator)
            elif not user.is_admin:
                exchange = await sync_to_async(Exchange.objects.get)(id=exchange_id)
                keyboard = InlineKeyboardBuilder()
                keyboard.add(InlineKeyboardButton(text="ДА!", callback_data=f"confirm_payed_kgs2{exchange.id}"))
                ask_review = "Оставите нам отзыв, пожалуйста? ❤"
                await callback_query.message.answer(text=ask_review, reply_markup=keyboard.as_markup())
        if validate == "kgs2":
            if user.is_admin:
                exchange = await sync_to_async(Exchange.objects.get)(id=exchange_id)
                payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)
                exchange.confirmed = True
                exchange.save()
                user = await sync_to_async(TelegramUser.objects.get)(user_id=exchange.user.user_id)
                referral = user.referred_by
                if exchange.balance_used is not None:
                    user = exchange.user
                    if user.balance == exchange.balance_used:
                        user.balance -= exchange.balance_used
                        user.save()
                if referral:
                    referral.balance += 40
                    referral.save()
                    await bot.send_message(referral.user_id, text=f"Пользователь *{user.username}* воспользовался "
                                           f"обменкой\n\nВам начислен бонус ввиде *40* сом!\nПоздравляю! 🎉")
                validate_text = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                       kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                       full=int(exchange.kgs_amount + payment.coms))
                if exchange.balance_used is not None:
                    validate_text = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                           kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                           full=int(exchange.kgs_amount + payment.coms - user.balance))
                    validate_text += f"\n🚩 *Использован баланс* `{user.balance}`_с_"
                keyboard = InlineKeyboardBuilder()
                keyboard.add(InlineKeyboardButton(text="Написать", callback_data=f"take_order_{exchange.user.user_id}"))
                validate_text += "\n\n✅✅✅ *Подтверждено*"
                await callback_query.message.edit_text(text=validate_text, reply_markup=keyboard.as_markup())

            elif not user.is_admin:
                await callback_query.message.delete()
                await bot.send_message(user.user_id, "Прошу, напиши классный отзыв!)) 🌞")

    if callback_query.data == "order_history":

        page = 1  # Начальная страница
        page_size = 3  # Количество отзывов на странице
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchanges = await sync_to_async(Exchange.objects.filter)(operator=user, confirmed=True)
        total_pages = (len(exchanges) + page_size - 1) // page_size
        print("PAGE", page, "TOTAL PAGE", total_pages)
        if page <= total_pages:
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            exchanges = exchanges[start_index:end_index]
            response_text = f"📔 Ваши заказы (страница {page} из {total_pages}):\n\n"
            for i, exchange in enumerate(exchanges, start=start_index + 1):
                payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)
                text_id = f"Заказ {exchange.id}\n"
                response_text += text_id
                response_text += text.order_data_short.format(amount=exchange.amount, crypto=exchange.crypto,
                                                        kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                        full=exchange.kgs_amount)
            builder = InlineKeyboardBuilder()
            if page > 1:
                builder.add(InlineKeyboardButton(text="Предыдущая", callback_data=f"exchange_prev_page_{page}"))
            if page < total_pages:
                builder.add(InlineKeyboardButton(text="Следующая", callback_data=f"exchange_next_page_{page}"))
            builder.add(InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase"))
            a = (1, 1) if not page > 1 or not page < total_pages else (2, 1)
            builder.adjust(*a)
            await callback_query.message.answer(text=response_text, reply_markup=builder.as_markup())
        if not exchanges:
            await callback_query.answer("Вы не совершили ниодного обмена!")

    if callback_query.data.startswith("exchange_next_page_"):
        page = int(callback_query.data.split("_")[3])

        print("NEXT PAGE EXCHANGE", page)
        page = int(page)
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)

        await get_exchange_history(callback_query.message, page + 1, user)
    if callback_query.data.startswith("exchange_prev_page_"):
        page = callback_query.data[19:]
        page = int(page)
        print("PREV PAGE EXCHANGE", page)
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        await get_exchange_history(callback_query.message, page - 1, user)

    if callback_query.data == "balance":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        print("IN BALANCE", user.username)

        referred_users = await sync_to_async(TelegramUser.objects.filter)(referred_by=user)
        balance_text = "➨ ➨ ➨💲*BALANCE* ©️"
        balance_text += "\n\n🟡 *Вы пригласили* ➩ `{}` _пользователей_\n💰 *Баланс* ➩ `{}`\n\n👇 *Ваша реферальная ссылка* 👇 \n\n`{}`".format(
            referred_users.count(), user.balance, "https://t.me/BestChangeKgz_bot?start={}".format(user.id))
        balance_text += f"\n\n\n*Приглашай друзей и получай с них кэшбек!*\n\n_За каждого приглашенного друга_ *40* _сом_"
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Приглашенные пользователи", callback_data="show_referrals"))
        keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back"))
        keyboard.adjust(1, 1)

        await callback_query.message.edit_text(text=balance_text, reply_markup=keyboard.as_markup())

    if callback_query.data == "back":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        await callback_query.message.edit_text(text.greet_operator.format(name=callback_query.from_user.full_name) if user.is_admin
                   else text.greet.format(name=callback_query.from_user.full_name), reply_markup=kb.operator_i if user.is_admin
        else kb.menu, parse_mode=ParseMode.MARKDOWN)

    if callback_query.data.startswith("use_balance"):
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        exchange.balance_used = user.balance

        exchange.save()
        await callback_query.answer("Баланс успешно добавлен!")

        page = 1  # Начальная страница
        page_size = 1  # Количество отзывов на странице

        data = await state.get_data()
        operator_id = data.get("operator_id")

        print("DATA DATA DATA DATA", operator_id)

        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
        payments = await sync_to_async(Payment.objects.all)()

        total_pages = (len(payments) + page_size - 1) // page_size  # Кол-во страниц

        builder = InlineKeyboardBuilder()
        if operator_id:
            exchange.operator = await sync_to_async(TelegramUser.objects.get)(user_id=operator_id)
            exchange.save()
            chat = await sync_to_async(Order.objects.get)(operator=exchange.operator)
            chat.user.add(user)
            payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)

            print("SHOWING PAYMENT", payment.operator.username, payment.coms, payment.usdt)

            response_text = f"Пользователь {user.username}\n\n"

            response_text += text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                    kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                    full=exchange.kgs_amount + payment.coms - exchange.balance_used if
                                                    exchange.balance_used else exchange.kgs_amount + payment.coms)
            if user.balance > 0 and exchange.balance_used is None:
                builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
            if exchange.balance_used:
                if user.balance != exchange.balance_used:
                    builder.add(
                        InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
                response_text += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used} _сом_"
            response_text += text.order_payments.format(mbank=payment.mbank, optima=payment.optima)
            await state.set_state(Chat.user)
            await bot.send_message(chat_id=exchange.operator.user_id,
                                   text=f"Пользователь {user.username} присоединился в чат", parse_mode=None)
            await callback_query.message.edit_text("👍 Оператор с вами, просто пишите в чат, ждём фото чека \n\n" + text.order_data.format(
                amount=exchange.amount, crypto=exchange.crypto, kgs_amount=exchange.kgs_amount, coms=payment.coms,
                full=exchange.kgs_amount + payment.coms - exchange.balance_used if exchange.balance_used else
                exchange.kgs_amount + payment.coms, mbank=payment.mbank, optima=payment.optima),
                                 reply_markup=builder.as_markup())
        elif payments.count() == 1:
            payment = payments.first()
            response_text = f""
            response_text += text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                    kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                    full=exchange.kgs_amount + payment.coms - exchange.balance_used if
                                                    exchange.balance_used else exchange.kgs_amount + payment.coms)
            if user.balance > 0 and exchange.balance_used is None:
                builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
            if exchange.balance_used:
                if user.balance != exchange.balance_used:
                    builder.add(
                        InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))

                response_text += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used} _сом_"
            response_text += text.order_payments.format(mbank=payment.mbank, optima=payment.optima)
            activity_text = await format_last_activity(payment.operator.last_activity)
            response_text += "\n\nПоследняя активность {}".format(activity_text)

            builder.add(
                InlineKeyboardButton(text="Подтверждаю",
                                     callback_data=f"confirm_purchase_{exchange.crypto} {payment.id}"),
                InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase"))
            await state.clear()
            await callback_query.message.edit_text(text=response_text, reply_markup=builder.as_markup())
        elif page < total_pages:
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            payment = payments[start_index:end_index]
            payment = payment[0]
            print("СКОЛЬКО ШТУК", payment)

            print("SHOWING PAYMENT", payment.operator.username, payment.coms, payment.usdt)
            response_text = f"Выберите реквизиты (страница {page} из {total_pages}):\n\n"
            response_text += text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                    kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                    full=exchange.kgs_amount + payment.coms - exchange.balance_used if
                                                    exchange.balance_used else exchange.kgs_amount + payment.coms)
            if user.balance > 0 and exchange.balance_used is None:
                builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
            if exchange.balance_used:
                if user.balance != exchange.balance_used:
                    builder.add(
                        InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
                response_text += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used} _сом_"
            response_text += text.order_payments.format(mbank=payment.mbank, optima=payment.optima)
            activity_text = await format_last_activity(payment.operator.last_activity)
            response_text += "\n\nПоследняя активность {}".format(activity_text)
            builder.add(InlineKeyboardButton(text="Подтверждаю", callback_data=f"confirm_purchase_ltc{payment.id}"))
            if page > 1:
                builder.add(InlineKeyboardButton(text="Предыдущая", callback_data=f"prev_page_{page}"))
            if page < total_pages:
                builder.add(InlineKeyboardButton(text="Следующая", callback_data=f"next_page_{page}"))
            builder.add(InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase"))
            a = (1, 1, 1) if not page > 1 or not page < total_pages else (1, 1, 2)
            builder.adjust(*a)
            await state.clear()
            await callback_query.message.edit_text(text=response_text, reply_markup=builder.as_markup())

    if callback_query.data == "show_referrals":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        referrals = await sync_to_async(TelegramUser.objects.filter)(referred_by=user)
        referrals_text = ""
        count = 1
        for i in referrals:
            referrals_text += f"{count}. @{i.username}"
        await callback_query.message.answer(text=referrals_text if referrals else "У вас нет приглаенных друзей")

    if callback_query.data == "promo-code-user":
        await callback_query.message.answer("Введите промокод")
        await state.set_state(PromoCodeUser.awaiting_promo)

    if callback_query.data == "promo-code-admin":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin:
            await callback_query.message.answer("Пишите сумму $ для промо кода")
            await state.set_state(PromoCodeAdmin.awaiting_sum)


@router.message(PromoCodeAdmin.awaiting_sum)
async def create_promo(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin:
            sum_of_promo = msg.text
            promo = await sync_to_async(Promo.objects.create)(amount=sum_of_promo)
            await msg.answer(f"Вы создали промокод: `{promo.promo_text}`\nСумма ${sum_of_promo}")
            await state.clear()
    except Exception as e:
        await msg.answer("Введите вверный формат, например число")


@router.message(PromoCodeUser.awaiting_promo)
async def add_promo_to_balance(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        promo_code = msg.text
        promo = await sync_to_async(Promo.objects.get)(promo_text=promo_code)
        if not promo.used:
            user.balance += promo.amount
            user.save()
            promo.used = True
            promo.save()
            await msg.answer(f"${promo.amount} добавлен в ваш баланс")
            await state.clear()
    except Exception as e:
        await msg.answer("Неверный промокод")


@router.message(BuyCryptoStates.awaiting_crypto_amount)
async def get_payments(message: Message, state: FSMContext, bot: Bot):
    page = 1  # Начальная страница
    page_size = 1  # Количество отзывов на странице

    data = await state.get_data()
    operator_id = data.get("operator_id")
    balance_used = data.get("balance")
    print("DATA DATA DATA DATA", operator_id)

    user = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
    exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
    payments = await sync_to_async(Payment.objects.all)()

    total_pages = (len(payments) + page_size - 1) // page_size  # Кол-во страниц

    builder = InlineKeyboardBuilder()
    if operator_id:
        exchange.operator = await sync_to_async(TelegramUser.objects.get)(user_id=operator_id)
        exchange.save()
        chat = await sync_to_async(Order.objects.get)(operator=exchange.operator)
        chat.user.add(user)
        crypto_amount = float(message.text)
        payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)
        crypto_price = await get_crypto_price(str(exchange.crypto), payment.usdt)
        total_cost = crypto_amount * crypto_price
        print("SHOWING PAYMENT", payment.operator.username, payment.coms, payment.usdt)
        exchange.amount = crypto_amount
        exchange.kgs_amount = total_cost
        exchange.exchange_rate = crypto_price
        exchange.save()

        response_text = text.order_data.format(amount=crypto_amount, crypto=exchange.crypto.upper(),
                                                kgs_amount=int(exchange.kgs_amount), coms=payment.coms,
                                                full=int(exchange.kgs_amount + payment.coms))
        if user.balance > 0 and exchange.balance_used is None:
            builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
            builder.adjust(1, 2)
        if exchange.balance_used:
            if user.balance != exchange.balance_used:
                builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
            response_text = text.order_data.format(amount=crypto_amount, crypto=exchange.crypto.upper(), kgs_amount=exchange.kgs_amount,
                                                coms=payment.coms, full=int(exchange.kgs_amount + payment.coms - exchange.balance_used))
            response_text += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used}"
        response_text += text.order_payments.format(mbank=payment.mbank, optima=payment.optima)
        response_text += f"\n \n✅☑️☑️ *ЧЕК*"
        builder.add(InlineKeyboardButton(text="Оплатил", callback_data="payed"))
        builder.add(InlineKeyboardButton(text="Отмена", callback_data="cencel_purchase_operator"))
        await state.set_state(Chat.user)
        await message.answer(text=response_text, reply_markup=builder.as_markup())
        await bot.send_message(chat_id=exchange.operator.user_id,
                               text=response_text + f"\n\nПользователь *{user.username}* присоединился в чат")
        await asyncio.sleep(3)
        await message.answer("Здравствуйте, оператор на связи, можете писать чат.")

    elif payments.count() == 1:
        payment = payments.first()
        crypto_amount = float(message.text)
        crypto_price = await get_crypto_price(str(exchange.crypto), payment.usdt)
        total_cost = crypto_amount * crypto_price
        print("SHOWING PAYMENT", payment.operator.username, payment.coms, payment.usdt)
        exchange.amount = crypto_amount
        exchange.kgs_amount = total_cost
        exchange.exchange_rate = crypto_price
        exchange.save()
        response_text = f""
        response_text += text.order_data.format(amount=crypto_amount, crypto=exchange.crypto.upper(),
                                                kgs_amount=int(exchange.kgs_amount), coms=payment.coms,
                                                full=int(exchange.kgs_amount + payment.coms))
        if user.balance > 0 and exchange.balance_used is None:
            builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
        if exchange.balance_used:
            if user.balance != exchange.balance_used:
                builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
            response_text = text.order_data.format(amount=crypto_amount, crypto=exchange.crypto.upper(),
                                                   kgs_amount=exchange.kgs_amount,
                                                   coms=payment.coms,
                                                   full=int(exchange.kgs_amount + payment.coms - exchange.balance_used))
            response_text += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used}"
        response_text += text.order_payments.format(mbank=payment.mbank,optima=payment.optima)
        activity_text = await format_last_activity(payment.operator.last_activity)
        response_text += "\n\nПоследняя активность {}".format(activity_text)

        builder.add(
            InlineKeyboardButton(text="Подтверждаю", callback_data=f"confirm_purchase_{exchange.crypto} {payment.id}"),
                    InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase"))
        builder.adjust(1, 2 if user.balance > 0 and exchange.balance_used is None else 2)
        await state.clear()
        await message.answer(text=response_text, reply_markup=builder.as_markup())
    elif page < total_pages:
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        payment = payments[start_index:end_index]
        payment = payment[0]
        print("СКОЛЬКО ШТУК", payment)
        crypto_amount = float(message.text)
        crypto_price = await get_crypto_price(str(exchange.crypto), payment.usdt)
        total_cost = crypto_amount * crypto_price
        print("SHOWING PAYMENT", payment.operator.username, payment.coms, payment.usdt)
        exchange.amount = crypto_amount
        exchange.kgs_amount = total_cost
        exchange.exchange_rate = crypto_price
        exchange.save()

        response_text = f"Выберите реквизиты (страница {page} из {total_pages}):\n\n"
        response_text += text.order_data.format(amount=crypto_amount, crypto=exchange.crypto.upper(),
                                                kgs_amount=(exchange.kgs_amount), coms=payment.coms,
                                                full=int(exchange.kgs_amount + payment.coms))
        if user.balance > 0 and exchange.balance_used is None:
            builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))

        if exchange.balance_used:
            if user.balance != exchange.balance_used:
                builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
            response_text = text.order_data.format(amount=crypto_amount, crypto=exchange.crypto.upper(),
                                                   kgs_amount=exchange.kgs_amount,
                                                   coms=payment.coms,
                                                   full=int(exchange.kgs_amount + payment.coms - exchange.balance_used))
            response_text += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used}"
        response_text += text.order_payments.format(mbank=payment.mbank, optima=payment.optima)
        activity_text = await format_last_activity(payment.operator.last_activity)
        response_text += "\n\nПоследняя активность {}".format(activity_text)
        builder.add(InlineKeyboardButton(text="Подтверждаю", callback_data=f"confirm_purchase_ltc{payment.id}"))
        if page > 1:
            builder.add(InlineKeyboardButton(text="Предыдущая", callback_data=f"prev_page_{page}"))
        if page < total_pages:
            builder.add(InlineKeyboardButton(text="Следующая", callback_data=f"next_page_{page}"))
        builder.add(InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase"))
        a = (1, 1, 1) if not page > 1 or not page < total_pages else (1, 1, 2)
        builder.adjust(*a)
        await state.clear()
        await message.answer(text=response_text, reply_markup=builder.as_markup())


async def get_exchange_history(message, page, user):
    page_size = 3  # Количество отзывов на странице
    exchanges = await sync_to_async(Exchange.objects.filter)(operator=user, confirmed=True)
    total_pages = (len(exchanges) + page_size - 1) // page_size

    if page <= total_pages:
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        exchanges = exchanges[start_index:end_index]
        exchange = exchanges.first()
        payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)
        print("EXCHANGES", exchanges)

        response_text = f"Реквизиты (страница {page} из {total_pages}):\n\n"
        builder = InlineKeyboardBuilder()
        if user.balance > 0 and exchange.balance_used is None:
            builder.add(InlineKeyboardButton(text="Использовать баланс", callback_data=f"use_balance{payment.id}"))
        for i, exchange in enumerate(exchanges, start=start_index + 1):
            text_id = f"Заказ {exchange.id}\n"
            print(text_id)
            response_text += text_id
            print("SHOWING PAYMENT", payment.operator.username, payment.coms, payment.usdt)
            response_text += text.order_data_short.format(amount=exchange.amount, crypto=exchange.crypto.upper(),
                                                          kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                          full=exchange.kgs_amount)

        if page > 1:
            builder.add(InlineKeyboardButton(text="Предыдущая", callback_data=f"exchange_prev_page_{page}"))
        if page < total_pages:
            builder.add(InlineKeyboardButton(text="Следующая", callback_data=f"exchange_next_page_{page}"))
        builder.add(InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase"))
        a = (1, 1) if not page > 1 or not page < total_pages else (2, 1)
        builder.adjust(*a)
        await message.edit_text(text=response_text, reply_markup=builder.as_markup())
    else:
        await message.answer("Страницы с отзывами не существует.")


async def get_reviews_page(message, page, user):
    page_size = 1  # Количество отзывов на странице
    exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
    payments = await sync_to_async(Payment.objects.all)()

    total_pages = (len(payments) + page_size - 1) // page_size

    if page <= total_pages:
        start_index = page - 1
        end_index = start_index + page_size
        payments_page = payments[start_index:end_index]

        response_text = f"Реквизиты (страница {page} из {total_pages}):\n\n"
        builder = InlineKeyboardBuilder()
        for i, payment in enumerate(payments_page, start=start_index + 1):
            crypto_price = await get_crypto_price(str(exchange.crypto), payment.usdt)
            total_cost = float(exchange.amount) * crypto_price
            exchange.kgs_amount = total_cost
            exchange.exchange_rate = crypto_price
            exchange.save()
            print("SHOWING PAYMENT", payment.operator.username, payment.coms, payment.usdt)
            response_text += text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                    kgs_amount=int(exchange.kgs_amount), coms=payment.coms,
                                                    full=int(exchange.kgs_amount + payment.coms))
            if exchange.balance_used:
                response_text = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                        kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                        full=int(exchange.kgs_amount + payment.coms - exchange.balance_used))
                response_text += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used}"
            builder.add(InlineKeyboardButton(text="Подтверждаю", callback_data=f"confirm_purchase_{exchange.crypto}"
                                f"{payment.id}"))
        if page > 1:
            builder.add(InlineKeyboardButton(text="Предыдущая", callback_data=f"prev_page_{page}"))
        if page < total_pages:
            builder.add(InlineKeyboardButton(text="Следующая", callback_data=f"next_page_{page}"))
        builder.add(InlineKeyboardButton(text="Отмена", callback_data="cancel_purchase"))
        a = (1, 1, 1) if not page > 1 or not page < total_pages else (1, 2, 1)
        builder.adjust(*a)
        await message.edit_text(text=response_text, reply_markup=builder.as_markup())
    else:
        await message.answer("Страницы с отзывами не существует.")


@router.message(Chat.user)
async def user_chat(msg: Message, state: FSMContext, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
    tg_message, created = await sync_to_async(TGMessage.objects.get_or_create)(message_id=msg.message_id, sender=user)
    if msg.text:
        tg_message.text = msg.text
        tg_message.save()
    photo = msg.photo
    print("PHOTO", photo)
    user.last_activity = timezone.now()
    user.save()
    orders = await sync_to_async(Order.objects.filter)(is_active=True)
    user_in_chat, chat_operator = await return_bool(user)
    if exchange.operator and not user_in_chat:
        print("ИФ ЭКСЧЕЙНДЖ ОПЕРАТОР")
        order = await sync_to_async(Order.objects.get)(operator=exchange.operator, is_active=True)
        order.user.add(user)
        order.save()
        tg_message.order = order
        tg_message.save()
        await msg.forward(exchange.operator.user_id)
        print("IF USER IN CHAT")
    if photo is not None:
        print("В ФОТКАХ")
        exchange.user_photo = photo[0].file_id
        exchange.save()
        payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(text="Деньги получены?", callback_data=f"confirm_payed_kgs1{exchange.id}"))
        chat_text = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                full=int(exchange.kgs_amount + payment.coms))
        chat_text += "\n\n✅☑️☑️ *CHECK*"
        await msg.forward(exchange.operator.user_id)
        await bot.send_message(exchange.operator.user_id, text=chat_text, reply_markup=keyboard.as_markup())
    elif user_in_chat:
        await msg.forward(chat_operator.user_id)
    elif not user_in_chat:
        for i in orders:
            await msg.forward(i.operator.user_id)


@router.message(Chat.operator)
async def chat_operator(message: types.Message, state: FSMContext, bot: Bot):
    operator = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
    order = await sync_to_async(Order.objects.get)(operator=operator, is_active=True)
    replied_message = message.reply_to_message
    photo = message.photo
    tg_message, created = await sync_to_async(TGMessage.objects.get_or_create)(message_id=message.message_id, sender=operator)
    if message.text:
        tg_message.text = message.text
        tg_message.save()
    if photo is not None:
        users = order.user.all()
        users = users.order_by('-last_activity')
        newest_user = users.first()
        exchange = Exchange.objects.filter(user=newest_user).latest('created_at')
        exchange.operator_photo = photo[0].file_id
        exchange.save()
        payment = await sync_to_async(Payment.objects.get)(operator=operator)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(text="Деньги получены?", callback_data=f"confirm_payed_kgs1{exchange.id}"))
        try:
            if replied_message:
                tg_message = await sync_to_async(TGMessage.objects.get)(message_id=replied_message.message_id - 1)
                await bot.send_photo(tg_message.sender.user_id, photo=exchange.operator_photo, caption=text.order_data.format(
                    amount=exchange.amount, crypto=exchange.crypto, kgs_amount=exchange.kgs_amount, coms=payment.coms,
                    full=exchange.kgs_amount + payment.coms, mbank=payment.mbank, optima=payment.optima),
                                     reply_markup=keyboard.as_markup())
                await bot.send_message(newest_user.user_id, message.text)
                return
            await bot.send_photo(newest_user.user_id, photo=exchange.operator_photo, caption=text.order_data.format(
                amount=exchange.amount, crypto=exchange.crypto, kgs_amount=exchange.kgs_amount, coms=payment.coms,
                full=exchange.kgs_amount + payment.coms, mbank=payment.mbank, optima=payment.optima),
                                   reply_markup=keyboard.as_markup())
        except Exception as e:
            exchange = Exchange.objects.filter(user=newest_user, confirmed=True).latest('created_at')
            exchange.operator_photo = photo[0].file_id
            exchange.save()
            if replied_message:
                tg_message = await sync_to_async(TGMessage.objects.get)(message_id=replied_message.message_id - 1)
                await bot.send_photo(tg_message.sender.user_id, photo=str(exchange.operator_photo), caption=text.order_data.format(
                    amount=exchange.amount, crypto=exchange.crypto, kgs_amount=exchange.kgs_amount, coms=payment.coms,
                    full=exchange.kgs_amount + payment.coms, mbank=payment.mbank, optima=payment.optima),
                                     reply_markup=keyboard.as_markup())

                return
            await bot.send_photo(newest_user.user_id, photo=str(exchange.operator_photo), caption=text.order_data.format(
                amount=exchange.amount, crypto=exchange.crypto, kgs_amount=exchange.kgs_amount, coms=payment.coms,
                full=exchange.kgs_amount + payment.coms, mbank=payment.mbank, optima=payment.optima),
                                   reply_markup=keyboard.as_markup())
    elif message.text.startswith("◀️ Отп"):
        users = order.user.all()
        users = users.order_by('-last_activity')
        newest_user = users.first()
        exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=newest_user, confirmed=False)
        exchange.operator = operator
        exchange.save()
        try:
            payment = await sync_to_async(Payment.objects.get)(operator=operator)
            text_to_user = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                  kgs_amount=int(exchange.kgs_amount), coms=payment.coms,
                                                  full=int(exchange.kgs_amount + payment.coms))

            if replied_message:
                tg_message = await sync_to_async(TGMessage.objects.get)(message_id=replied_message.message_id - 1)
                exchange = await sync_to_async(Exchange.objects.get)(user=tg_message.sender, confirmed=False)
                if exchange.balance_used is not None:
                    text_to_user = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                          kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                          full=int(exchange.kgs_amount + payment.coms - exchange.balance_used))
                    text_to_user += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used}"
                order.user.add(tg_message.sender)
                order.save()
                await bot.send_message(chat_id=tg_message.sender.user_id, text=text_to_user,
                                       reply_markup=kb.bought_ltc_operator)
                await message.delete()
                await message.answer(text="Кнопки отправлены\n")
            else:
                if exchange.balance_used is not None:
                    text_to_user = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                          kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                          full=int(exchange.kgs_amount + payment.coms - exchange.balance_used))
                    text_to_user += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used}"
                await bot.send_message(chat_id=newest_user.user_id, text=text_to_user,
                                       reply_markup=kb.bought_ltc_operator)
                await message.answer(text="ВЫ ОТПРАВИЛИ ЕМУ ОРДЕР:\n" + text_to_user)
        except Exception:
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(text="LTC", callback_data="buy_ltc"))
            keyboard.add(InlineKeyboardButton(text="BTC", callback_data="buy_btc"))
            keyboard.adjust(1, 1)
            await bot.send_message(newest_user.user_id, "Оператор отправил вам кнопки 👌\n"
                                                        "Пожалуйста выберите что хотите купить",
                                   reply_markup=keyboard.as_markup())
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
    print(text_to_send)

    users = await sync_to_async(TelegramUser.objects.all)()
    response_text = ""
    for user in users:
        try:
            chat_member = await bot.get_chat_member(user.user_id, user.user_id)
            if chat_member.status not in ["left", "kicked", "restricted"]:
                # Пользователь не заблокировал бота, отправляем сообщение
                await bot.send_message(user.user_id, text_to_send, parse_mode=None)
                response_text += f"Сообщение отправлено пользователю: {user.username}\n"
            else:
                await message.answer(f"Сообщение НЕ отправлено: {user.username}")
                print(f"Пользователь {user.username} заблокировал бота")
        except Exception as e:
            await message.answer(response_text)
            print(f"Ошибка при отправке сообщения пользователю {user.username}: {str(e)}")

    await message.answer(f"Вы отправили сообщение:\n\n{text_to_send}\n\nвсем пользователям в боте.")
    await state.clear()


# @router.message(Command("users"))
# async def send_users(msg: Message):
#     user_id = msg.from_user.id
#     username = msg.from_user.username
#
#     user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
#         user_id=user_id,
#         username=username
#     )
#     if user.is_admin:
#         users = await sync_to_async(TelegramUser.objects.all)()
#         count = 1
#         response_text = ""
#         for user in users:
#             if user.is_admin:
#                 response_text += f"{count} {user.username} ------ HAS ADMIN PERMISSIONS\n"
#                 count += 1
#             else:
#                 response_text += f"{count} {user.username}\m"
#                 count += 1

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
        response_text = ""

        for user in users:
            chat_member = await bot.get_chat_member(user.user_id, user.user_id)
            if chat_member.status not in ["left", "kicked", "restricted"]:
                if user.is_admin:
                    response_text += f"{count} {user.username if user.username else user.user_id} ------ HAS ADMIN PERMISSIONS\n"
                else:
                    response_text += f"{count} {user.username if user.username else user.user_id}\n"
                count += 1
    
                # Отправляем сообщение с информацией о пользователях каждые 50 пользователей
                if count % 50 == 0:
                    await msg.answer(response_text)
                    response_text = ""

        # Отправляем оставшуюся часть сообщения, если есть
        if response_text:
            await msg.answer(response_text)

        # Сообщение о завершении расчёта
        await msg.answer("Расчёт пользователей завершён.")


@router.message(Command("permission"))
async def add_permission(msg: Message, state: FSMContext):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        user_id=msg.from_user.id,
    )
    if user.is_admin:
        await state.set_state(OperatorAdd.awaiting_user_id)
    else:
        await msg.answer("Нет прав")


@router.message(OperatorAdd.awaiting_user_id)
async def awaiting_user_id(msg: Message, state: FSMContext):
    try:
        username = msg.text
        print(username)
        if username.startswith("@"):
            username = username[1:]
        user, _ = await sync_to_async(TelegramUser.objects.get_or_create)(username=username)
        print("QUERYSET", user.username)
        if not user.is_admin:
            user.is_admin = True
            user.save()
            await msg.answer(f"Пользователь {user.username} ✓ добавлен в операторы", parse_mode=None)
            await state.clear()
        elif user.is_admin:
            user.is_admin = False
            user.save()
            await msg.answer(f"Пользователь {user.username} ✕ удалён из операторов", parse_mode=None)
            await state.clear()
    except Exception as e:
        print(e)
        await msg.answer("✖ Произошла ошибка, введите вверный *username*")


@router.message(SendStateOperator.awaiting_coms)
@router.message(SendStateOperator.awaiting_usdt)
async def awaiting_usdt(msg: Message, state: FSMContext):
    try:
        current_state = await state.get_state()
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        course = await sync_to_async(Payment.objects.get)(operator=user)
        if current_state == 'SendStateOperator:awaiting_usdt':
            print("IN CURRENT STATE", current_state)
            new_usdt = msg.text
            course.usdt = new_usdt
            course.save()
            await msg.delete()
            await msg.answer(f"Курс изменён на {new_usdt}")
            await state.clear()
        elif current_state == 'SendStateOperator:awaiting_coms':
            new_coms = msg.text
            course.coms = new_coms
            course.save()
            await msg.delete()
            await msg.answer(f"Комиссия изменена на {new_coms}")
            await state.clear()

    except Exception:
        await msg.delete()
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


@router.message(UserPayed.awaiting_photo)
async def awaiting_payed_photo(msg: Message, state: FSMContext, bot: Bot):
    photo = msg.photo
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=user, confirmed=False)
    payment = await sync_to_async(Payment.objects.get)(operator=exchange.operator)

    if photo:
        exchange.user_photo = photo[0].file_id
        exchange.save()
        awaiting_photo = "❓ *ПОДТВЕРДИТЕ ПОЛУЧЕНИЕ СРЕДСТВ*\n\n"
        awaiting_photo += text.order_data.format(crypto=exchange.crypto.upper(), amount=exchange.amount,
                                                kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                full=int(exchange.kgs_amount + payment.coms))
        if exchange.balance_used is not None:
            awaiting_photo = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                full=int(exchange.kgs_amount + payment.coms - user.balance))
            awaiting_photo += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used} _сом_"

        awaiting_photo += "\n\n✅☑️☑️ *CHECK*"
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="Деньги получены?", callback_data=f"confirm_payed_kgs1{exchange.id}"))
        keyboard.add(InlineKeyboardButton(text="Написать", callback_data=f"take_order_{msg.from_user.id}"))
        await msg.answer("Пожалуйста введите адрес кошелька")
        await msg.forward(exchange.operator.user_id)

        await state.set_state(Chat.user)
        await bot.send_message(exchange.operator.user_id,text=awaiting_photo, reply_markup=keyboard.as_markup())


@router.message()
async def state_holder(message: Message, state: FSMContext, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
    user.last_activity = timezone.now()
    user.save()
    print(message.new_chat_members)
    current_state = await state.get_state()
    if not current_state:
        if user.is_admin:
            order = await sync_to_async(Order.objects.get)(operator=user)
            if message.text:
                replied_message = message.reply_to_message
                if message.text.startswith("◀️ Отп"):
                    users = order.user.all()
                    users = users.order_by('-last_activity')
                    newest_user = users.first()
                    exchange, _ = await sync_to_async(Exchange.objects.get_or_create)(user=newest_user, confirmed=False)
                    exchange.operator = user
                    exchange.save()
                    try:
                        payment = await sync_to_async(Payment.objects.get)(operator=user)
                        text_to_user = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                              kgs_amount=int(exchange.kgs_amount), coms=payment.coms,
                                                              full=int(exchange.kgs_amount + payment.coms))

                        if replied_message:
                            tg_message = await sync_to_async(TGMessage.objects.get)(
                                message_id=replied_message.message_id - 1)
                            exchange = await sync_to_async(Exchange.objects.get)(user=tg_message.sender, confirmed=False)
                            if exchange.balance_used is not None:
                                text_to_user = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                                      kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                                      full=int(
                                                                          exchange.kgs_amount + payment.coms - exchange.balance_used))
                                text_to_user += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used}"
                            order.user.add(tg_message.sender)
                            order.save()
                            await bot.send_message(chat_id=tg_message.sender.user_id, text=text_to_user,
                                                   reply_markup=kb.bought_ltc_operator)
                            await message.delete()
                            await message.answer(text="Кнопки отправлены\n")
                        else:
                            if exchange.balance_used is not None:
                                text_to_user = text.order_data.format(amount=exchange.amount, crypto=exchange.crypto,
                                                                      kgs_amount=exchange.kgs_amount, coms=payment.coms,
                                                                      full=int(
                                                                          exchange.kgs_amount + payment.coms - exchange.balance_used))
                                text_to_user += f"\n🚩 *Использован баланс* 🟰 {exchange.balance_used}"
                            await bot.send_message(chat_id=newest_user.user_id, text=text_to_user,
                                                   reply_markup=kb.bought_ltc_operator)
                            await message.answer(text="ВЫ ОТПРАВИЛИ ЕМУ ОРДЕР:\n" + text_to_user)
                    except Exception as e:
                        keyboard = InlineKeyboardBuilder()
                        keyboard.add(InlineKeyboardButton(text="LTC", callback_data="buy_ltc"))
                        keyboard.add(InlineKeyboardButton(text="BTC", callback_data="buy_btc"))
                        keyboard.adjust(1, 1)
                        await bot.send_message(newest_user.user_id, "Оператор отправил вам кнопки 👌\n"
                                                                    "Пожалуйста выберите что хотите купить",
                                               reply_markup=keyboard.as_markup())
                    return
                order = await sync_to_async(Order.objects.get)(operator=user)
                users = order.user.all()
                users = users.order_by('-last_activity')
                newest_user = users.first()
                if newest_user is not None:
                    await bot.send_message(newest_user.user_id, message.text)
                await state.set_state(Chat.operator)
        # if not user.is_admin:
            # orders = await sync_to_async(Order.objects.all)()
            # user_in_chat, chat_operator = await return_bool(user)
            # await state.set_state(Chat.user)
            # if user_in_chat:
            #     await msg.forward(chat_operator.user_id)
            # if not user_in_chat:
            #     for i in orders:
            #         await msg.forward(i.operator.user_id)


