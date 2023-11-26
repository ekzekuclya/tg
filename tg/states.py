from aiogram.fsm.state import StatesGroup, State


class BuyCryptoStates(StatesGroup):
    awaiting_crypto_amount = State()


class SendState(StatesGroup):
    awaiting_text = State()
    awaiting_kvitto = State()


class SendStateOperator(StatesGroup):
    awaiting_usdt = State()
    awaiting_coms = State()


class PaymentState(StatesGroup):
    awaiting_mbank = State()
    awaiting_optima = State()


class Chat(StatesGroup):
    user = State()
    operator = State()
    user_id = []


class OperatorAdd(StatesGroup):
    awaiting_user_id = State()


class UserPayed(StatesGroup):
    awaiting_photo = State()


class PromoCodeUser(StatesGroup):
    awaiting_promo = State()


class PromoCodeAdmin(StatesGroup):
    awaiting_sum = State()

