import telebot
from config import BOT_TOKEN
from handlers.start_handler import StartHandler

bot = telebot.TeleBot(BOT_TOKEN)
start_handler = StartHandler(bot)

@bot.message_handler(commands=['start'])
def handle_start(message):
    start_handler.handle_start(message)

if __name__ == "__bot__":
    bot.polling(none_stop=True)