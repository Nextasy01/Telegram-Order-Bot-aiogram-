from aiogram import Bot, types
from SQLighter import SQLighter
from aiogram.utils.markdown import text
from aiogram.utils.emoji import emojize
from aiogram.utils.callback_data import CallbackData

posts_cb = CallbackData('post', 'action', 'id', 'tablename')

bot = Bot(token=TOKEN)
db_worker = SQLighter('orders.db')

def get_menu_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_1 = types.KeyboardButton(text=text(emojize(":writing_hand: Заказать")))
    button_2 = types.KeyboardButton(text=text(emojize(":clap: Помощь")))
    button_3 = types.KeyboardButton(text=text(emojize(":hammer_and_wrench: Настройки(только для администраторов)")))
    keyboard.add(button_1, button_2, button_3)
    return keyboard
