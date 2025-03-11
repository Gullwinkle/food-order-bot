from telebot import types
from models.user import User
from database.user_repository import UserRepository
from config import DB_NAME

class StartHandler:
    def __init__(self, bot):
        self.bot = bot
        self.user_repo = UserRepository(DB_NAME)

    def handle_start(self, message):
        user = User(
            telegram_id=message.chat.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        self.user_repo.add_user(user)

        inline_keyboard = types.InlineKeyboardMarkup()
        btn_restaurant = types.InlineKeyboardButton("Выбрать ресторан", callback_data="choose_restaurant")
        btn_profile = types.InlineKeyboardButton("Личный кабинет", callback_data="profile")
        inline_keyboard.add(btn_restaurant, btn_profile)

        self.bot.send_message(
            message.chat.id,
            f"Привет, {user.first_name}! Я бот, который поможет тебе заказать еду.",
            reply_markup=inline_keyboard
        )