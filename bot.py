import asyncio
import logging
import typing
import csv
import re
import os

from aiogram.utils.markdown import text
from aiogram.utils.emoji import emojize
from aiogram import types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import bot, db_worker, posts_cb, get_menu_keyboard
from handlers.admin import register_admin_handler

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Address(StatesGroup):
    address = State()


my_cart = []
tot_price = []
categories = ['burgers', 'pizzas']
pay_order = []

capt_name = ''
capt_price = ''  # lol

channel_name = '@tempfortemp'
link = 'https://t.me/tempfortemp'

@dp.message_handler(Text(equals=text(emojize("🔙 Назад в главное меню"))))
@dp.message_handler(commands=['start'])
async def start_bot(message: types.Message):
    msg_text = text(emojize('Здравстуйте! Этот бот для заказа еды, выберите кнопку :writing_hand: Заказать'))
    await message.answer(msg_text, reply_markup=get_menu_keyboard())

@dp.callback_query_handler(posts_cb.filter(action='want_this'))
async def put_to_cart(query: types.CallbackQuery, callback_data: typing.Dict):
    order_id = callback_data['id']
    order_category = callback_data['tablename']
    order = db_worker.get_name(order_category, order_id)
    db_worker.add_new_order(query.from_user.id, order_id, order_category)
    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, f'Ваш заказ {order[0]} добавлен в корзину!')

@dp.callback_query_handler(posts_cb.filter(action='pay'))
async def request_phone_num(query: types.CallbackQuery):
    kbd = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    phone_num_btn = types.KeyboardButton("📞 Отправить номер телефона", request_contact=True)
    go_back_btn = types.KeyboardButton("Отменить и вернуться назад")
    kbd.add(phone_num_btn, go_back_btn)
    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, "Отлично! Введите пожалуйста ваш "
                                               "номер телефона, чтобы "
                                               "наш курьер мог связаться с вами и сообщить о вашем заказе",
                           reply_markup=kbd)



@dp.message_handler(content_types=['contact'])
async def request_address(message: types.Message):
    del_kbd = types.ReplyKeyboardRemove()
    pay_order.append(message.contact.phone_number)
    await bot.send_message(message.chat.id, "Укажите пожалуйста ваш адрес", reply_markup=del_kbd)
    await Address.address.set()

@dp.message_handler(state=Address.address)
async def request_location(message: types.Message, state: FSMContext):
    kbd = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    phone_num_btn = types.KeyboardButton("📍 Отправить геопозицию", request_location=True)
    go_back_btn = types.KeyboardButton("Отменить и вернуться назад")
    kbd.add(phone_num_btn, go_back_btn)
    pay_order.append(message.text)

    await bot.send_message(message.chat.id, "Хорошо! А теперь отправьте вашу геопозицию", reply_markup=kbd)
    await state.finish()

@dp.message_handler(content_types=['location'])
async def pay_confirmation(message: types.Message):
    pay_order.append(message.location)
    db_worker.clear_all_orders(message.from_user.id)
    with open("all_orders.csv", "a", newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow([pay_order[2], pay_order[0], pay_order[1], pay_order[3], pay_order[4]])
        file.close()
    await bot.send_message(message.chat.id, "Ваш заказ оформлен! Ожидайте звонка курьера. Спасибо!")
    pay_order.clear()


@dp.callback_query_handler(posts_cb.filter(action='remove_cart'))
async def clean_all_from_cart(query: types.CallbackQuery):
    db_worker.clear_all_orders(query.from_user.id)
    await bot.answer_callback_query(query.id)
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                        reply_markup=None)
    await bot.send_message(query.from_user.id, 'Корзина очищена!')

@dp.message_handler(Text(equals=text("Отменить и вернуться назад")))
@dp.message_handler(Text(equals=text(emojize("🔙 Назад"))))
@dp.message_handler(Text(equals=text(emojize(":writing_hand: Заказать"))))
async def order_start(message: types.Message):
    pay_order.clear()
    new_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_1 = types.KeyboardButton(text=text(emojize("🍽 Блюда")))
    button_2 = types.KeyboardButton(text=text(emojize("🍹 Напитки")))
    button_3 = types.KeyboardButton(text=text(emojize("🍧 Десерты")))
    button_0 = types.KeyboardButton(text=text(emojize("🔙 Назад в главное меню")))
    new_keyboard.add(button_1, button_2, button_3, button_0)
    await message.reply(text(emojize("Что заказывать будем :smile:?")), reply_markup=new_keyboard)

@dp.message_handler(Text(equals=text(emojize("🔙 Назад к выбору блюд"))))
@dp.message_handler(Text(equals=text(emojize("🍽 Блюда"))))
async def order_meal(message: types.Message):
    new_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_1 = types.KeyboardButton(text=text(emojize("🍔 Бургеры")))
    button_2 = types.KeyboardButton(text=text(emojize("🍕 Пицца")))
    button_3 = types.KeyboardButton(text=text(emojize("🍲 Вторые блюда")))
    button_4 = types.KeyboardButton(text=text(emojize("🍜 Первые блюда")))
    button_0 = types.KeyboardButton(text=text(emojize("🔙 Назад")))
    new_keyboard.add(button_1, button_2, button_3, button_4, button_0)
    await message.reply(text(emojize("Какое блюдо вас интересует?")), reply_markup=new_keyboard)

@dp.message_handler(Text(equals=text(emojize("🛒 Корзина"))))
async def cart(message: types.Message):
    inl_kbd = types.InlineKeyboardMarkup()
    btn_clean = types.InlineKeyboardButton("❌ Очистить всю корзину",
                                           callback_data=posts_cb.new(action='remove_cart', id='-', tablename='-'))
    btn_pay = types.InlineKeyboardButton("✅ Оплатить", callback_data=posts_cb.new(action='pay', id='-', tablename='-'))
    inl_kbd.row(btn_clean, btn_pay)

    kbd = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_1 = types.KeyboardButton(text=text(emojize("🔙 Назад к выбору блюд")))
    kbd.add(button_1)

    await bot.send_message(message.chat.id, "Ваши заказы: ", reply_markup=kbd)
    for category in categories:
        orders = db_worker.get_orders(message.from_user.id, category)
        try:
         for order in orders:
            my_cart.append(order)
        except Exception as e:
            print(e)

    for category in categories:
        total_price = db_worker.get_total_price(message.from_user.id, category)
        try:
            for price in total_price:
                if price[0] is not None:
                 tot_price.append(price[0])
        except Exception as e:
            print(e)

    my_dict = {i: my_cart.count(i) for i in my_cart}
    orders = []
    for key in my_dict:
        orders.append(key[0] + " " + str(key[2]) + " шт")
        order_str = key[0] + ": " + str(key[1]) + " сум " + str(key[2]) + "шт."
        await bot.send_message(message.chat.id, "" + order_str)


    order_str1 = ""
    for order in orders:
        if len(orders) - 1 == orders.index(order):
            order_str1 = order_str1 + order + ""
            break
        order_str1 = order_str1 + order + ", "

    Sum = sum(tot_price)
    if Sum == 0:
        await bot.send_message(message.chat.id, "Общая стоимость вашего заказа: " + str(Sum) + " сум", reply_markup=None)
    else:
        await bot.send_message(message.chat.id, "Общая стоимость вашего заказа: " + str(Sum) + " сум",
                           reply_markup=inl_kbd)


    if not os.path.isfile('all_orders.csv'):
        list_of_lists = ["Phone Number", "Order", "Price", "Address", "Location"]
        with open("all_orders.csv", "w", newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(list_of_lists)
            file.close()


    pay_order.append(order_str1)
    pay_order.append(str(Sum))

    my_cart.clear()
    tot_price.clear()

@dp.message_handler(Text(equals=text(emojize("🍔 Бургеры"))))
async def order_burgers(message: types.Message):
    reply_kbd = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_my_orders = types.KeyboardButton(text=text(emojize("🛒 Корзина")))
    btn_back = types.KeyboardButton(text=text(emojize("🔙 Назад к выбору блюд")))
    reply_kbd.add(btn_back, btn_my_orders)

    burger_id = db_worker.get_id_from_table('burgers')
    borgirs = db_worker.get_pics_from_table('burgers')
    names = db_worker.get_names_from_table('burgers')
    price = db_worker.get_price_from_table('burgers')
    c = 0
    await bot.send_message(message.chat.id, "Вот, пожалуйста!", reply_markup=reply_kbd)
    for burger in borgirs:
        keyboard = types.InlineKeyboardMarkup()
        btn_order = types.InlineKeyboardButton("Хочу!",
                                               callback_data=posts_cb.new(action='want_this', id=burger_id[c][0], tablename='burgers'))
        keyboard.insert(btn_order)
        await bot.send_photo(message.chat.id, burger[0], caption=names[c][0] + '\n' + str(price[c][0]) + ' сум', reply_markup=keyboard)
        c = c + 1


@dp.message_handler(Text(equals=text(emojize("🍕 Пицца"))))
async def order_pizzas(message: types.Message):
    reply_kbd = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_my_orders = types.KeyboardButton(text=text(emojize("🛒 Корзина")))
    btn_back = types.KeyboardButton(text=text(emojize("🔙 Назад к выбору блюд")))
    reply_kbd.add(btn_back, btn_my_orders)

    keyboard = types.InlineKeyboardMarkup()
    btn_order = types.KeyboardButton("Хочу!")
    keyboard.add(btn_order)

    pizza_id = db_worker.get_id_from_table('pizzas')
    pizzas = db_worker.get_pics_from_table('pizzas')
    names = db_worker.get_names_from_table('pizzas')
    price = db_worker.get_price_from_table('pizzas')

    c = 0
    await bot.send_message(message.chat.id, "Вот, пожалуйста!", reply_markup=reply_kbd)
    for pizza in pizzas:
        keyboard = types.InlineKeyboardMarkup()
        btn_order = types.InlineKeyboardButton("Хочу!",
                                               callback_data=posts_cb.new(action='want_this', id=pizza_id[c][0], tablename='pizzas'))
        keyboard.insert(btn_order)
        await bot.send_photo(message.chat.id, pizza[0], caption=names[c][0] + '\n' + str(price[c][0]) + ' сум', reply_markup=keyboard)
        c = c + 1

async def scheduled(wait_for):
    while True:
        await asyncio.sleep(wait_for)
        if os.path.isfile("all_orders.csv"):
            with open("all_orders.csv", "r", newline='') as file:
                reader = csv.reader(file, delimiter=';')
                line_count = 0
                for row in reader:
                    if line_count == 0:
                        line_count += 1
                    else:
                        print(row[0])
                        a = re.split(r',', row[4])
                        latitude = re.sub(r'[^0-9.]', '', a[0])
                        longitude = re.sub(r'[^0-9.]', '', a[1])
                        lol = await bot.send_message(chat_id=channel_name, text=f"НОВЫЙ ЗАКАЗ!!!\n"
                                                                          f"{row[0]}\n"
                                                                          f"{row[1]}\n"
                                                                          f"{row[2]} сум\n"
                                                                          f"{row[3]}")

                        await bot.send_location(channel_name, float(latitude), float(longitude),
                                                reply_to_message_id=lol.message_id)
                        line_count += 1
                file.close()

            with open("all_orders.csv", "r", newline='') as file:
                reader = csv.reader(file, delimiter=';')
                data = list(reader)
                row_count = len(data)
                file.close()
                if row_count > 1:
                    os.remove("all_orders.csv")


if __name__ == "__main__":
    register_admin_handler(dp)
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled(5))
    executor.start_polling(dp)
