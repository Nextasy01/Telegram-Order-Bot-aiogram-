import typing
import logging

from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram import types
from aiogram.utils.markdown import text
from aiogram.utils.emoji import emojize
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import bot, db_worker, posts_cb, get_menu_keyboard

chat_info = []
new_order = []


class Mode(StatesGroup):
    start = State()
    try_admin = State()
    admin = State()
    customer = State()
    wrong_pass = State()

class AddItem(StatesGroup):
    name = State()
    price = State()
    photo = State()

class EditItem(StatesGroup):
    name = State()
    price = State()
    photo = State()


def get_admin_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_1 = types.KeyboardButton(text=text(emojize("📝 Добавить в меню")))
    button_2 = types.KeyboardButton(text=text(emojize("✏ Редактировать меню")))
    button_3 = types.KeyboardButton(text=text(emojize("❌ Удалить")))
    button_0 = types.KeyboardButton(text=text(emojize("🚪 Выход")))
    keyboard.add(button_1, button_2, button_3, button_0)
    return keyboard

async def request_admin(message: types.Message):
    remove_rpl_keyboard = types.ReplyKeyboardRemove()
    inline_keyboard = types.InlineKeyboardMarkup()
    cancel_button = types.InlineKeyboardButton("🔙 Назад", callback_data=posts_cb.new(action='back_to_menu', id='-', tablename='-'))
    inline_keyboard.add(cancel_button)
    await Mode.try_admin.set()
    await message.answer("Connecting to admin mode...", reply_markup=remove_rpl_keyboard)
    await message.answer("Введите пароль:", reply_markup=inline_keyboard)

async def query_menu(query: types.CallbackQuery):
    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, 'Возвращаюсь в главное меню', reply_markup=get_menu_keyboard())

async def add_to_menu(query: types.CallbackQuery, callback_data: typing.Dict):
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                        reply_markup=None)
    category = callback_data['tablename']
    new_order.append(category)
    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, 'Введите имя нового товара')
    await AddItem.name.set()


async def add_name(message: types.Message):
    new_order.append(message.text)
    await bot.send_message(message.chat.id, "Укажите цену в сумах")
    await AddItem.price.set()

async def add_price(message: types.Message):
    new_order.append(int(message.text))
    await bot.send_message(message.chat.id, "Пришлите фото товара")
    await AddItem.photo.set()


async def add_photo(message: types.Message):
    inln_kbd = types.InlineKeyboardMarkup()
    btn_1 = types.InlineKeyboardButton('➕ Добавить еще товар', callback_data=posts_cb.new(action='add_more', id='-', tablename='-'))
    btn_2 = types.InlineKeyboardButton('🔙 Назад', callback_data=posts_cb.new(action='back', id='-', tablename='-'))
    inln_kbd.row(btn_1, btn_2)
    new_order.append(message.photo[-1].file_id)
    db_worker.insert_product(new_order[0], new_order[1], new_order[2], new_order[3])
    await bot.send_message(message.chat.id, 'Товар добавлен!', reply_markup=inln_kbd)
    await Mode.admin.set()
    new_order.clear()

async def edit_menu(query: types.CallbackQuery, callback_data: typing.Dict):
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                        reply_markup=None)
    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, "Выберите товар который хотите изменить")

    category = callback_data['tablename']
    item_id = db_worker.get_id_from_table(category)
    items = db_worker.get_pics_from_table(category)
    names = db_worker.get_names_from_table(category)
    price = db_worker.get_price_from_table(category)
    c = 0
    for item in items:
        keyboard = types.InlineKeyboardMarkup()
        btn_edit_name = types.InlineKeyboardButton("🔤 Изменить название",
                                                callback_data=posts_cb.new(action='edit_name', id=item_id[c][0],
                                                                           tablename=category))
        btn_edit_price = types.InlineKeyboardButton("💰 Изменить цену",
                                                   callback_data=posts_cb.new(action='edit_price', id=item_id[c][0],
                                                                              tablename=category))
        btn_edit_pic = types.InlineKeyboardButton("🖼 Изменить картинку",
                                                   callback_data=posts_cb.new(action='edit_pic', id=item_id[c][0],
                                                                              tablename=category))
        keyboard.add(btn_edit_name, btn_edit_price, btn_edit_pic)
        await bot.send_photo(query.from_user.id, item[0], caption=names[c][0] + '\n' + str(price[c][0]) + ' сум',
                             reply_markup=keyboard)
        c = c + 1

async def call_edit_name(query: types.CallbackQuery, callback_data: typing.Dict):
    new_order.append(callback_data['tablename'])
    new_order.append(callback_data['id'])

    chat_info.append(query.message.chat.id)
    chat_info.append(query.message.message_id)

    global capt_price
    capt_price = db_worker.get_price(new_order[0], new_order[1])

    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, 'Укажите новое имя')
    await EditItem.name.set()

async def edit_name(message: types.Message):
    new_order.append(message.text)
    db_worker.update_product_name(new_order[0], new_order[1], new_order[2])

    # kbd = types.InlineKeyboardMarkup()
    # btn_edit_name = types.InlineKeyboardButton("🔤 Изменить название",
    #                                            callback_data=posts_cb.new(action='edit_name', id=item_id[c][0],
    #                                                                       tablename=category))
    # btn_edit_price = types.InlineKeyboardButton("💰 Изменить цену",
    #                                             callback_data=posts_cb.new(action='edit_price', id=item_id[c][0],
    #                                                                        tablename=category))
    # btn_edit_pic = types.InlineKeyboardButton("🖼 Изменить картинку",
    #                                           callback_data=posts_cb.new(action='edit_pic', id=item_id[c][0],
    #                                                                      tablename=category))
    # kbd.add(btn_edit_name, btn_edit_price, btn_edit_pic)

    await bot.send_message(message.chat.id, 'Имя товара изменено успешно!')
    await bot.edit_message_caption(chat_id=chat_info[0], message_id=chat_info[1], caption=new_order[2] + '\n' + str(capt_price[0]) + ' сум')
    await Mode.admin.set()

    chat_info.clear()
    new_order.clear()

async def call_edit_price(query: types.CallbackQuery, callback_data: typing.Dict):
    new_order.append(callback_data['tablename'])
    new_order.append(callback_data['id'])

    chat_info.append(query.message.chat.id)
    chat_info.append(query.message.message_id)

    global capt_name
    capt_name = db_worker.get_name(new_order[0], new_order[1])

    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, 'Укажите новую цену')
    await EditItem.price.set()

async def edit_price(message: types.Message):
    new_order.append(int(message.text))
    db_worker.update_product_price(new_order[0], new_order[1], new_order[2])
    await bot.send_message(message.chat.id, 'Цена товара изменена успешно!')
    await bot.edit_message_caption(chat_id=chat_info[0], message_id=chat_info[1], caption=capt_name[0] + '\n' + str(new_order[2]) + ' сум')
    await Mode.admin.set()
    chat_info.clear()
    new_order.clear()

async def call_edit_pic(query: types.CallbackQuery, callback_data: typing.Dict):
    new_order.append(callback_data['tablename'])
    new_order.append(callback_data['id'])

    chat_info.append(query.message.chat.id)
    chat_info.append(query.message.message_id)

    global capt_name
    capt_name = db_worker.get_name(new_order[0], new_order[1])

    global capt_price
    capt_price = db_worker.get_price(new_order[0], new_order[1])

    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, 'Отправьте новую картинку')
    await EditItem.photo.set()

async def edit_photo(message: types.Message):
    new_order.append(message.photo[-1].file_id)
    db_worker.update_product_pic(new_order[0], new_order[1], new_order[2])

    await bot.send_message(message.chat.id, 'Фото товара изменено успешно!')
    await bot.edit_message_media(chat_id=chat_info[0], message_id=chat_info[1], media=types.InputMediaPhoto(new_order[2]))
    await bot.edit_message_caption(chat_id=chat_info[0], message_id=chat_info[1], caption=capt_name[0] + '\n' + str(capt_price[0]) + ' сум')
    await Mode.admin.set()

    chat_info.clear()
    new_order.clear()

async def remove_from_menu(query: types.CallbackQuery, callback_data: typing.Dict):
    category = callback_data['tablename']
    ID = callback_data['id']
    db_worker.delete_product(category, ID)
    await bot.delete_message(chat_id=query.message.chat.id, message_id=
                             query.message.message_id)
    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, "Выбранный товар удалён!")

async def show_to_remove(query: types.CallbackQuery, callback_data: typing.Dict):
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                        reply_markup=None)
    await bot.answer_callback_query(query.id)
    await bot.send_message(query.from_user.id, "Выберите товар который хотите удалить")

    category = callback_data['tablename']
    item_id = db_worker.get_id_from_table(category)
    items = db_worker.get_pics_from_table(category)
    names = db_worker.get_names_from_table(category)
    price = db_worker.get_price_from_table(category)
    c = 0
    for item in items:
        keyboard = types.InlineKeyboardMarkup()
        btn_delete = types.InlineKeyboardButton("❌ Удалить",
                                               callback_data=posts_cb.new(action='remove', id=item_id[c][0],
                                                                          tablename=category))
        keyboard.insert(btn_delete)
        await bot.send_photo(query.from_user.id, item[0], caption=names[c][0] + '\n' + str(price[c][0]) + ' сум',
                             reply_markup=keyboard)
        c = c + 1

async def deny_admin_access(message: types.Message):
    await message.answer("Неверный пароль!")

async def admin_mode_inln(query: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                        reply_markup=None)
    await bot.send_message(query.from_user.id, "Возвращаюсь в меню", reply_markup=get_admin_keyboard())

async def admin_mode_rpl(message: types.Message):
    await bot.send_message(message.chat.id, "Возвращаюсь в меню", reply_markup=get_admin_keyboard())

async def admin_mode(message: types.Message, state: FSMContext):
     await Mode.admin.set()
     async with state.proxy() as data:
         data['password'] = message.text

     await message.answer("You entered admin mode!", reply_markup=get_admin_keyboard())

async def admin_add_more(query: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                        reply_markup=None)
    inline_kbd = types.InlineKeyboardMarkup()
    inline_btn_meal_1 = types.InlineKeyboardButton('🍔 Бургеры', callback_data=posts_cb.new(action='add', id='-',
                                                                                            tablename='burgers'))
    inline_btn_meal_2 = types.InlineKeyboardButton('🍕 Пицца',
                                                   callback_data=posts_cb.new(action='add', id='-', tablename='pizzas'))
    inline_kbd.row(inline_btn_meal_1, inline_btn_meal_2)
    await bot.send_message(query.from_user.id, "Выберите категорию:", reply_markup=inline_kbd)

async def admin_add(message: types.Message):
    rpl_kbd = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_1 = types.KeyboardButton(text=text(emojize("🔙 Назад в меню")))
    rpl_kbd.add(btn_1)

    inline_kbd = types.InlineKeyboardMarkup()
    inline_btn_meal_1 = types.InlineKeyboardButton('🍔 Бургеры', callback_data=posts_cb.new(action='add', id='-', tablename='burgers'))
    inline_btn_meal_2 = types.InlineKeyboardButton('🍕 Пицца', callback_data=posts_cb.new(action='add', id='-', tablename='pizzas'))
    inline_kbd.row(inline_btn_meal_1, inline_btn_meal_2)
    await bot.send_message(message.chat.id, "Что хотите добавить в меню?", reply_markup=rpl_kbd)
    await bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=inline_kbd)

async def admin_edit(message: types.Message):
    rpl_kbd = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_1 = types.KeyboardButton(text=text(emojize("🔙 Назад в меню")))
    rpl_kbd.add(btn_1)

    inline_kbd = types.InlineKeyboardMarkup()
    inline_btn_meal_1 = types.InlineKeyboardButton('🍔 Бургеры', callback_data=posts_cb.new(action='edit', id='-',
                                                                                            tablename='burgers'))
    inline_btn_meal_2 = types.InlineKeyboardButton('🍕 Пицца',
                                                   callback_data=posts_cb.new(action='edit', id='-', tablename='pizzas'))
    inline_kbd.row(inline_btn_meal_1, inline_btn_meal_2)
    await bot.send_message(message.chat.id, "Какой товар хотите изменить?", reply_markup=rpl_kbd)
    await bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=inline_kbd)

async def admin_remove(message: types.Message):
    rpl_kbd = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_1 = types.KeyboardButton(text=text(emojize("🔙 Назад в меню")))
    rpl_kbd.add(btn_1)

    inline_kbd = types.InlineKeyboardMarkup()
    inline_btn_meal_1 = types.InlineKeyboardButton('🍔 Бургеры', callback_data=posts_cb.new(action='show', id='-',
                                                                                            tablename='burgers'))
    inline_btn_meal_2 = types.InlineKeyboardButton('🍕 Пицца',
                                                   callback_data=posts_cb.new(action='show', id='-', tablename='pizzas'))
    inline_kbd.row(inline_btn_meal_1, inline_btn_meal_2)

    await bot.send_message(message.chat.id, "Какой товар хотите удалить?", reply_markup=rpl_kbd)
    await bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=inline_kbd)

async def cancel_admin(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Exitting admin mode', reply_markup=types.ReplyKeyboardRemove())
    await message.answer('Введите /start чтобы вернуться в начальное меню')


def register_admin_handler(dp: Dispatcher):
    dp.register_message_handler(request_admin, Text(equals=text(emojize(":hammer_and_wrench: Настройки(только для администраторов)"))))
    dp.register_callback_query_handler(query_menu, posts_cb.filter(action='back_to_menu'), state=Mode.try_admin)
    dp.register_callback_query_handler(add_to_menu, posts_cb.filter(action='add'), state=Mode.admin)

    dp.register_message_handler(add_name, (lambda message: True if message.text is not None else False),
                    state=AddItem.name)
    dp.register_message_handler(add_price, (lambda message: True if message.text is not None else False),
                    state=AddItem.price)
    dp.register_message_handler(add_photo, (lambda message: True if message.photo[-1] is not None else False),
                    state=AddItem.photo, content_types=['photo'])

    dp.register_callback_query_handler(edit_menu, posts_cb.filter(action='edit'), state=Mode.admin)
    dp.register_callback_query_handler(call_edit_name, posts_cb.filter(action='edit_name'), state=Mode.admin)
    dp.register_message_handler(edit_name, (lambda message: True if message.text is not None else False),
                    state=EditItem.name)
    dp.register_callback_query_handler(call_edit_price, posts_cb.filter(action='edit_price'), state=Mode.admin)
    dp.register_message_handler(edit_price, (lambda message: True if message.text is not None else False),
                    state=EditItem.price)
    dp.register_callback_query_handler(call_edit_pic, posts_cb.filter(action='edit_pic'), state=Mode.admin)
    dp.register_message_handler(edit_photo, (lambda message: True if message.photo[-1] is not None else False),
                    state=EditItem.photo, content_types=['photo'])

    dp.register_callback_query_handler(remove_from_menu, posts_cb.filter(action='remove'), state=Mode.admin)
    dp.register_callback_query_handler(show_to_remove, posts_cb.filter(action='show'), state=Mode.admin)

    dp.register_message_handler(deny_admin_access, (lambda message: True if message.text != "12345678" else False),
                    state=Mode.try_admin)
    dp.register_callback_query_handler(admin_mode_inln, posts_cb.filter(action='back'), state=Mode.admin)
    dp.register_message_handler(admin_mode_rpl, Text(equals=text(emojize("🔙 Назад в меню"))), state=Mode.admin)
    dp.register_message_handler(admin_mode, (lambda message: True if message.text == "12345678" else False),
                    state=Mode.try_admin)
    dp.register_callback_query_handler(admin_add_more, posts_cb.filter(action='add_more'), state=Mode.admin)
    dp.register_message_handler(admin_add, Text(equals=text(emojize("📝 Добавить в меню"))),state=Mode.admin)
    dp.register_message_handler(admin_edit, Text(equals=text(emojize("✏ Редактировать меню"))), state=Mode.admin)
    dp.register_message_handler(admin_remove, Text(equals=text(emojize("❌ Удалить"))), state=Mode.admin)
    dp.register_message_handler(cancel_admin, Text(equals=text(emojize("🚪 Выход"))),state=Mode.admin)