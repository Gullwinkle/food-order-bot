import telebot
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import os
from base import *

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

bot.set_my_commands([
    telebot.types.BotCommand("/start", "Начать работу с ботом")
])


user_states = {}
restaurants = get_restaurants()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.chat.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    username = message.from_user.first_name
    text = f"Привет, {username}! Я бот, который поможет тебе заказать еду."
    inline_keyboard = InlineKeyboardMarkup()
    btn_restaurant = InlineKeyboardButton("Выбрать ресторан", callback_data="choose_restaurant")
    btn_profile = InlineKeyboardButton("Личный кабинет", callback_data="profile")
    inline_keyboard.add(btn_restaurant, btn_profile)
    bot.send_message(message.chat.id, text, reply_markup=inline_keyboard)


@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("waiting_for") == "address")
def handle_address(message):
    # Получаем адрес пользователя
    user_address = message.text
    bot.delete_message(message.chat.id, user_states[message.chat.id]["del_message_id"])
    bot.delete_message(message.chat.id, message.message_id)
    add_user_address(message.chat.id, user_address)
    send_user_profile(message.from_user.id)
    user_states[message.chat.id]["del_message_id"] = None
    user_states[message.chat.id]["waiting_for"] = None

@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get("waiting_for") == "rest_feedback")
def handle_rest_feedback(message):
    # Получаем отзыв пользователя
    user_feedback = message.text
    bot.delete_message(message.chat.id, user_states[message.chat.id]["del_message_id"])
    bot.delete_message(message.chat.id, message.message_id)
    add_rest_comment(message.chat.id, user_feedback)
    send_user_profile(message.from_user.id)
    user_states[message.chat.id]["del_message_id"] = None
    user_states[message.chat.id]["waiting_for"] = None

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    user_id = call.message.chat.id
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if user_id not in user_states:
        user_states[user_id] = {"restaurant_index": 0, "dish_index": 0, "category_id": None, "dishes": [],
                                "dishes_len": 0, "waiting_for": None, "del_message_id": None}

    if call.data.startswith("category"):
        category_id = int(call.data.split("|")[1])
        user_states[user_id]["category_id"] = category_id
        user_states[user_id]["dish_index"] = 0
        user_states[user_id]["dishes"] = get_dishes(category_id)
        user_states[user_id]["dishes_len"] = len(user_states[user_id]["dishes"])
        send_category_info(user_id)

    elif call.data.startswith("ask_rating"):
        order_id = call.data.split("|")[1]
        rate_rest(user_id, order_id)

    elif call.data.startswith("feedback"):
        order_id = int(call.data.split("|")[1])
        rating = int(call.data.split("|")[2])
        restaurant_id = get_rest_id(order_id)
        add_rest_rating(call.from_user.id, restaurant_id, order_id, rating)
        ask_feedback(user_id)

    elif call.data == "choose_restaurant":
        user_states[user_id]["restaurant_index"] = 0
        send_restaurant_info(user_id)

    elif call.data == "prev_restaurant":
        user_states[user_id]["restaurant_index"] = (user_states[user_id]["restaurant_index"] - 1) % len(restaurants)
        send_restaurant_info(call.message.chat.id)

    elif call.data == "next_restaurant":
        user_states[user_id]["restaurant_index"] = (user_states[user_id]["restaurant_index"] + 1) % len(restaurants)
        send_restaurant_info(call.message.chat.id)

    elif call.data == "select_restaurant":
        send_menu(call.message.chat.id)

    elif call.data == "prev_dish":
        user_states[user_id]["dish_index"] = (user_states[user_id]["dish_index"] - 1) % user_states[user_id]["dishes_len"]
        send_category_info(call.message.chat.id)

    elif call.data == "next_dish":
        user_states[user_id]["dish_index"] = (user_states[user_id]["dish_index"] + 1) % user_states[user_id]["dishes_len"]
        send_category_info(call.message.chat.id)

    elif call.data == "add_dish":
        add_to_cart(call.from_user.id, user_states[user_id]["dishes"][user_states[user_id]["dish_index"]]["id"],
                    user_states[user_id]["dishes"][user_states[user_id]["dish_index"]]["price"],
                    restaurants[user_states[user_id]["restaurant_index"]]["id"])
        send_category_info(call.message.chat.id)

    elif call.data == "cart":
        send_cart(call.message.chat.id)

    elif call.data == "back_to_start":
        send_welcome_directly(call.from_user)

    elif call.data == "confirm_order":
        send_payment_options(call.message.chat.id)

    elif call.data == "pay_online":
        process_online_payment(call.message.chat.id)

    elif call.data == "profile":
        send_user_profile(call.from_user.id)

    elif call.data == "order_history":
        send_user_orders(call.message.chat.id)

    elif call.data == "pay_cash":
        process_cash_payment(call.message.chat.id)

    elif call.data == "cancel_order":
        cancel_order(call.message.chat.id)

    elif call.data == "rest_feedback":
        rest_feedback(call.from_user.id)

    elif call.data == "add_address":
        msg = bot.send_message(call.message.chat.id, "Введите адрес доставки:")
        user_states[call.message.chat.id]["waiting_for"] = "address"
        user_states[call.message.chat.id]["del_message_id"] = msg.message_id


def send_restaurant_info(user_id):
    inline_keyboard = InlineKeyboardMarkup()
    btn_prev = InlineKeyboardButton("Пред.", callback_data="prev_restaurant")
    btn_next = InlineKeyboardButton("След.", callback_data="next_restaurant")
    btn_select = InlineKeyboardButton("Выбрать", callback_data="select_restaurant")
    btn_back = InlineKeyboardButton("Назад", callback_data="back_to_start")
    inline_keyboard.row(btn_prev, btn_next)
    inline_keyboard.row(btn_select)
    inline_keyboard.row(btn_back)
    ratings = get_rest_fb(restaurants[user_states[user_id]['restaurant_index']]["id"])
    avg_rating = ratings[0]
    rating_count = ratings[1]
    text = f"Ресторан: {restaurants[user_states[user_id]['restaurant_index']]['name']}\n" \
           f"Описание: {restaurants[user_states[user_id]['restaurant_index']]['description']}\n" \
           f"Рейтинг: {round(avg_rating, 2)}  Отзывов: {rating_count}\n"
    bot.send_photo(user_id, photo=open(restaurants[user_states[user_id]['restaurant_index']]["logo"], "rb"), caption=text,
                   reply_markup=inline_keyboard)

def send_menu(user_id):
    restaurant = restaurants[user_states[user_id]["restaurant_index"]]["id"]
    categories = get_categories(restaurant)
    inline_keyboard = InlineKeyboardMarkup()
    for button in categories:
        inline_keyboard.add(InlineKeyboardButton(button["name"], callback_data="category" + "|" + str(button["id"])))
    btn_back = InlineKeyboardButton("Назад", callback_data="choose_restaurant")
    inline_keyboard.row(btn_back)

    bot.send_photo(user_id, photo=open(restaurants[user_states[user_id]['restaurant_index']]["logo"], "rb"),
                   caption="Выберите категорию:",
                   reply_markup=inline_keyboard)


def send_category_info(user_id):
    inline_keyboard = InlineKeyboardMarkup()
    btn_prev = InlineKeyboardButton("Пред.", callback_data="prev_dish")
    btn_next = InlineKeyboardButton("След.", callback_data="next_dish")
    btn_add = InlineKeyboardButton("Добавить в заказ", callback_data="add_dish")
    btn_cart = InlineKeyboardButton("Корзина", callback_data="cart")
    btn_back = InlineKeyboardButton("Назад", callback_data="select_restaurant")
    text = (f"{user_states[user_id]['dishes'][user_states[user_id]['dish_index']]['name']} - {user_states[user_id]['dishes'][user_states[user_id]['dish_index']]['price']} руб.\n"
            f" {user_states[user_id]['dishes'][user_states[user_id]['dish_index']]['description']}")
    inline_keyboard.row(btn_prev, btn_next)
    inline_keyboard.row(btn_add)
    inline_keyboard.row(btn_cart, btn_back)
    bot.send_photo(user_id, photo=open(user_states[user_id]['dishes'][user_states[user_id]['dish_index']]["image"], "rb"), caption=text,
                   reply_markup=inline_keyboard)

def send_cart(user_id):
    order_id = get_current_order_id(user_id)
    if order_id[1] != 'new':
        inline_keyboard = InlineKeyboardMarkup()
        btn_back = InlineKeyboardButton("Назад", callback_data="category" + "|" + str(user_states[user_id]['category_id']))
        inline_keyboard.row(btn_back)
        bot.send_message(user_id, "Ваша корзина пуста.", reply_markup=inline_keyboard)
        return
    order = get_order_items(order_id[0])
    text = "Ваш заказ:\n"
    for dish in order:
        text += f"{dish['dish_name']} - {dish['quantity']} шт. - {dish['total']} руб.\n"
    text += f"\nОбщая стоимость: {sum([dish['total'] for dish in order])} руб."
    inline_keyboard = InlineKeyboardMarkup()
    btn_confirm = InlineKeyboardButton("Подтвердить заказ", callback_data="confirm_order")
    btn_cancel = InlineKeyboardButton("Отменить заказ", callback_data="cancel_order")
    btn_back = InlineKeyboardButton("Назад", callback_data="category" + "|" + str(user_states[user_id]['category_id']))
    inline_keyboard.row(btn_confirm)
    inline_keyboard.row(btn_cancel)
    inline_keyboard.row(btn_back)
    bot.send_message(user_id, text, reply_markup=inline_keyboard)


def send_payment_options(user_id):
    order_id = get_current_order_id(user_id)[0]
    order = get_order_items(order_id)
    if not order[0]["dish_name"]:
        bot.send_message(user_id, "Ваша корзина пуста.")
        return
    text = "Ваш заказ:\n"
    for dish in order:
        text += f"{dish['dish_name']} - {dish['quantity']} шт. - {dish['total']} руб.\n"
    text += f"\nСумма к оплате: {sum([dish['total'] for dish in order])} руб."
    text += "\nВыберите способ оплаты:"
    change_order_status(user_id, "confirmed")
    inline_keyboard = InlineKeyboardMarkup()
    btn_online = InlineKeyboardButton("Оплата онлайн", callback_data="pay_online")
    btn_cash = InlineKeyboardButton("Оплата наличными", callback_data="pay_cash")
    inline_keyboard.row(btn_online, btn_cash)
    bot.send_message(user_id, text, reply_markup=inline_keyboard)


def process_online_payment(user_id):
    order_id = get_current_order_id(user_id)[0]
    change_order_status(user_id, "paid")
    change_order_payment_method(order_id, "online")
    inline_keyboard = InlineKeyboardMarkup()
    btn_restaurant = InlineKeyboardButton("Выбрать ресторан", callback_data="choose_restaurant")
    btn_profile = InlineKeyboardButton("Личный кабинет", callback_data="profile")
    inline_keyboard.add(btn_restaurant, btn_profile)
    bot.send_message(user_id, f"Оплата прошла успешно! Ваш заказ оформлен.\n Номер вашего заказа: {order_id}", reply_markup=inline_keyboard)


def process_cash_payment(user_id):
    order_id = get_current_order_id(user_id)[0]
    change_order_status(user_id, "paid")
    change_order_payment_method(order_id, "cash")
    inline_keyboard = InlineKeyboardMarkup()
    btn_restaurant = InlineKeyboardButton("Выбрать ресторан", callback_data="choose_restaurant")
    btn_profile = InlineKeyboardButton("Личный кабинет", callback_data="profile")
    inline_keyboard.add(btn_restaurant, btn_profile)
    bot.send_message(user_id, f"Ваш заказ оформлен. Оплата наличными при получении.\n Номер вашего заказа: {order_id}", reply_markup=inline_keyboard)


def send_user_profile(user_id):
    address = get_user_address(user_id)
    username = get_username(user_id)[0]
    text = f"Имя пользователя: {username}\nАдрес доставки: {address[0][0]}"
    inline_keyboard = InlineKeyboardMarkup()

    if not address[0][0]:
        btn_add_adr = InlineKeyboardButton("Добавить адрес доставки", callback_data="add_address")
        inline_keyboard.row(btn_add_adr)
    else:
        btn_add_adr = InlineKeyboardButton("Изменить адрес доставки", callback_data="add_address")
        inline_keyboard.row(btn_add_adr)

    btn_orders = InlineKeyboardButton("История заказов", callback_data="order_history")
    btn_back = InlineKeyboardButton("Назад", callback_data="back_to_start")
    inline_keyboard.row(btn_orders)
    inline_keyboard.row(btn_back)
    bot.send_message(user_id, text, reply_markup=inline_keyboard)


def send_user_orders(user_id): # История заказов
    user_orders = get_user_orders(user_id)

    if not user_orders:
        inline_keyboard = InlineKeyboardMarkup()
        btn_profile = InlineKeyboardButton("Назад", callback_data="profile")
        inline_keyboard.add(btn_profile)
        bot.send_message(user_id, "У вас нет заказов.", reply_markup=inline_keyboard)
    else:
        text = "Ваши заказы:\n"
        for order in user_orders:
            text += f"заказ от {order['updated_at']} - {order['status']} - {order['total_cost']} руб. - {order['payment_method']}\n"
        inline_keyboard = InlineKeyboardMarkup()
        btn_profile = InlineKeyboardButton("Назад", callback_data="profile")
        btn_feedback = InlineKeyboardButton("Оценить заказ", callback_data="rest_feedback")
        inline_keyboard.add(btn_feedback)
        inline_keyboard.add(btn_profile)
        bot.send_message(user_id, text, reply_markup=inline_keyboard)


def rest_feedback(user_id): # Всё для отзыва
    user_orders = get_user_unrated_orders(user_id)
    user_states[user_id]["waiting_for"] = None
    user_states[user_id]["del_message_id"] = None
    text = "Ваши заказы, на которые можно оставить отзыв:\n"
    for order in user_orders:
        text += f"{order['id']}. заказ от {order['updated_at']} из {order['name']} - {order['total_cost']} руб.\n"

    inline_keyboard = InlineKeyboardMarkup()
    for button in user_orders:
        inline_keyboard.add(InlineKeyboardButton(button['id'], callback_data="ask_rating" + "|" + str(button["id"])))

    btn_profile = InlineKeyboardButton("Назад", callback_data="profile")
    inline_keyboard.add(btn_profile)
    text += "Выберете номер заказа для оценки"

    bot.send_message(user_id, text, reply_markup=inline_keyboard)


def rate_rest(user_id, order_id): # Отзыв получаем и отправляем БД
    inline_keyboard = InlineKeyboardMarkup()
    btn_1 = InlineKeyboardButton("1⭐️", callback_data="feedback" + "|" + str(order_id) + "|" + "1")
    btn_2 = InlineKeyboardButton("2⭐️", callback_data="feedback" + "|" + str(order_id) + "|" + "2")
    btn_3 = InlineKeyboardButton("3⭐️", callback_data="feedback" + "|" + str(order_id) + "|" + "3")
    btn_4 = InlineKeyboardButton("4⭐️", callback_data="feedback" + "|" + str(order_id) + "|" + "4")
    btn_5 = InlineKeyboardButton("5⭐️", callback_data="feedback" + "|" + str(order_id) + "|" + "5")
    btn_profile = InlineKeyboardButton("Назад", callback_data="rest_feedback")
    btn_feedback = InlineKeyboardButton("Оценить другой заказ", callback_data="rest_feedback")
    inline_keyboard.row(btn_1, btn_2, btn_3, btn_4, btn_5)
    inline_keyboard.row(btn_feedback)
    inline_keyboard.row(btn_profile)
    text = f'Оцените ваш заказ из {get_rest_name(order_id)[0]}: \n'
    order = get_order_items(order_id)
    for dish in order:
        text += f"{dish['dish_name']} - {dish['quantity']} шт. - {dish['total']} руб.\n"
    bot.send_message(user_id, text, reply_markup=inline_keyboard)


def ask_feedback(user_id):
    inline_keyboard = InlineKeyboardMarkup()
    user_states[user_id]["waiting_for"] = "rest_feedback"
    btn_back = InlineKeyboardButton("Назад", callback_data="rest_feedback")
    inline_keyboard.add(btn_back)
    msg = bot.send_message(user_id, "Спасибо за оценку! Вы можете оставить отзыв, отправив сообщение:", reply_markup=inline_keyboard)
    user_states[user_id]["del_message_id"] = msg.message_id

def cancel_order(user_id):
    change_order_status(user_id, "canceled")
    inline_keyboard = InlineKeyboardMarkup()
    btn_restaurant = InlineKeyboardButton("Выбрать ресторан", callback_data="choose_restaurant")
    btn_profile = InlineKeyboardButton("Личный кабинет", callback_data="profile")
    inline_keyboard.add(btn_restaurant, btn_profile)
    bot.send_message(user_id, "Ваш заказ отменен. Вы можете выбрать другой ресторан.", reply_markup=inline_keyboard)


def send_welcome_directly(user):
    username = user.first_name
    text = f"Привет, {username}! Я бот, который поможет тебе заказать еду."
    inline_keyboard = InlineKeyboardMarkup()
    btn_restaurant = InlineKeyboardButton("Выбрать ресторан", callback_data="choose_restaurant")
    btn_profile = InlineKeyboardButton("Личный кабинет", callback_data="profile")
    inline_keyboard.add(btn_restaurant, btn_profile)
    bot.send_message(user.id, text, reply_markup=inline_keyboard)


while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        time.sleep(15)  # Ожидание перед повторной попыткой
