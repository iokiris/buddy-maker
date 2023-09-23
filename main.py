from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from mtcnn import MTCNN
import numpy as np
detector = MTCNN()

from static.files import config

from utils.ml_splitter import ml_split_fields
from utils.db_controller import DataHandler, User

from utils.data import profiles

from utils import search_engine

from aiogram3_form import Form, FormField
import wrappers.registration_form as regform


API_TOKEN: str = config.TOKEN

bot: Bot = Bot(token=API_TOKEN)
dp: Dispatcher = Dispatcher()
router = Router()
dp.include_router(router)

class PersonForm(Form, router=router):
    first_name: str = FormField(
        enter_message_text="Как тебя зовут?",
        error_message_text="Ошибка"
    )
    age: int = FormField(
        enter_message_text="Сколько тебе лет?",
        error_message_text="Возраст должен быть числом!",
    )
    hometown: str = FormField(
        enter_message_text="Какой город для тебя родной?"
    )

class AboutMeForm(Form, router=router):
    info: str = FormField(
        enter_message_text = "Расскажите немного о себе! Достаточно нескольких предложений.",
        error_message_text = "Этого слишком мало! Добавьте чего-нибудь ещё",
        filter = (F.text.len() > 16) & F.text
    )

from PIL import Image, ImageChops, ImageDraw, ImageFont
from io import BytesIO

from tempfile import NamedTemporaryFile

@dp.message(F.photo)
async def photo_handler(message: Message, state: FSMContext):
    img = Image.new(mode="RGBA", size=(1920,1080))
    file_info = await bot.get_file(message.photo[-1].file_id)
    #with NamedTemporaryFile("wb", suffix=".png") as pct:

    downloaded_file = await bot.download_file(file_info.file_path)
    img = Image.open(downloaded_file)
    
    result = detector.detect_faces(np.asarray(img))
    

    if regform.States.users[message.chat.id]["photo"] == "":
        if len(result) >= 1:
            if (result[0]['confidence']) > 0.8:
                regform.States.users[message.chat.id]["photo"] = message.photo[-1].file_id
                confirm_button = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(
                text = "Подтвердить",
                callback_data = f"steps*next*1"
                )]])
                await message.delete()
                await message.answer_photo(
                    caption = "Ваше фото для анкеты:",
                    photo = message.photo[-1].file_id,
                    reply_markup = confirm_button
                )
                
        else:
            await message.answer(text = "Мы не уверены, что это фото с вашим лицом. Пожалуйста, пришлите другое.")
            #regform.States.users[message.chat.id]["photo"] = message.photo[-1].file_id    

'''@person_form.submit()
async def person_form_submit_handler(form: person_form, event_chat: types.Chat):
    #States.users[user_id][States.current_step(user_id)]
    States.users[user_id]["person"] = {
            "name": form.first_name,
            "age": form.age,
            "hometown": form.hometown,
            "visual": f"{form.first_name}, {form.age}. {form.hometown}"
        }

        confirm_button = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(
            text = "Подтвердить",
            callback_data = f"steps*next"
        )]])
        await message.answer(text = States.users[user_id]["person"]["visual"], reply_markup=confirm_button)
        await start_form_handler(user_id, message, person_form, bot, state)'''

#class PhotoForm(StatesGroup):
#    photo = State()

def get_form(name):
    return {
        "person": PersonForm,
        "about_me": AboutMeForm,
    }[name]

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    uid = message.chat.id
    #regform.States.current[uid] = "hobbies"
    user = await profiles.get_user(uid)
    if user:
        await message.answer(
            text = "Привет, это бот Buddy Maker. Я нашел твою анкету."
        )
        await message.answer_photo(
            photo = user.photo_id,
            caption = user.profile
        )
    else:
        await message.answer("Привет, это бот для более простых знакмоств в среде нашего вуза!")
        #await message.answer("Кратко описать возможности")
        await start_all_forms(uid, message, state)
    kb = [
        [
            types.KeyboardButton(text="Моя анкета"),
            types.KeyboardButton(text="Группы по интересам")
        ],
        [
            types.KeyboardButton(text="Собрать команду"),
            types.KeyboardButton(text="Случайное знакомство")
        ],
        [
            types.KeyboardButton(text="Родственная душа")
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите способ подачи"
    )




async def start_all_forms(uid, message: types.Message, state: FSMContext):
    await regform.gen_personal_form(uid, message, PersonForm, bot, state)
@dp.callback_query(F.data.split("*")[0] == "add")
async def add_user_field(callback: types.CallbackQuery, state: FSMContext):
    uid = callback.message.chat.id
    query = callback.data.split("*")
    field = query[1]
    match field:
        case "hobbies":
            await add_hobbie(uid, query[2])
            await callback.message.edit_text(
                text = f"Выбранные хобби: {', '.join(regform.States.get_value_from_key(uid, 'hobbies')['visual'])}",
                reply_markup=callback.message.reply_markup
            )
            return
        case "hobbies_cat":
            regform.States.users[uid]["hobbies"]["last_cat"] = query[2]
            regform.States.next_step(
                message = callback.message,
                user_id = uid,
                bot = bot,
                state = state
            )
            await regform.States.toggle_from_step_name(
                message = callback.message,
                user_id = uid,
                form = None,
                bot = bot,
                state = state
            )

async def send_sim_user(self_id, message):
    try:
        matched_user = await profiles.get_user((await search_engine.searcher(self_id, 1, 0.4, []))[0][0])
        await message.answer_photo(
            photo = matched_user.photo_id,
            caption = matched_user.profile,
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔎  Поиск", callback_data="search*sim")]])
        )
    except:
        await message.answer(text = "Я никого не нашёл :(")
@dp.message(F.text.lower() == "поиск")
async def find_sim(message: Message):
    uid = message.chat.id
    await send_sim_user(uid, message=message)
@dp.message(F.text.lower() == "моя анкета")
async def d(message: Message):
    user = await profiles.get_user(message.chat.id)
    if user:
        await message.answer_photo(
            caption = "Ваша анкета:\n" + user.profile,
            photo = user.photo_id,
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text = "Новая анкета", callback_data="profiles*pre-edit")
            ]])
        )
    else:
        await message.answer(text = "Анкеты не найдены.")

@dp.callback_query(F.data.split("*")[0] == "profiles")
async def profiles_mg(callback: types.CallbackQuery, state: FSMContext):
    query = callback.data.split("*")
    uid = callback.message.chat.id
    print(query)
    match query[1]:
        case "pre-edit":
            confirm_button = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(
                text = "Подтвердить",
                callback_data = f"profiles*delete"
            )]])
            await callback.message.answer(text = f"Ваша текущая анкета будет удалена.", reply_markup=confirm_button)
        case "delete":
            await profiles.remove_user(uid)
            await callback.message.edit_text(
                text = "Анкета удалена. Приступим к заполнению новой?",
                reply_markup = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text = "Заполнить анкету", callback_data = "profiles*new")]]))
        case "new":
            await start_all_forms(uid, callback.message, state)

@dp.callback_query(F.data == "back_cat")
async def add_user_field(callback: types.CallbackQuery, state: FSMContext):
    regform.States.prev_step(
            message = callback.message,
            user_id = callback.message.chat.id,
            bot = bot,
            state = state
        )

@dp.callback_query(F.data.split("*")[0] == "set")
async def set_user_field(callback: types.CallbackQuery):
    uid = callback.message.chat.id
    query = callback.data.split("*")
    field = query[1]
    match field:
        case "course":
            regform.States.users[uid]["study_info"]["course"] = int(query[2])
        case "dorm":
            if query[2] == "true":
                dorm_status = True
            else:
                dorm_status = False
            regform.States.users[uid]["study_info"]["lives_in_dorm"] = dorm_status
            
        case "institute":
            regform.States.users[uid]["study_info"]["institute"] = query[2]
    confirm_button = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(
                text = "Подтвердить",
                callback_data = f"steps*next*1"
            )]])
    await callback.message.edit_text(text = f"Выбрано: {query[-1]}", reply_markup=confirm_button)


async def add_hobbie(user_id, name):
    category = regform.States.get_value_from_key(user_id, "hobbies")["last_cat"]
    try:
        arr = regform.States.users[user_id]["hobbies"][category]
    except KeyError:
        arr = []
    varr = regform.States.users[user_id]["hobbies"]["visual"]
    if name not in arr:
        varr.append(name)
        arr.append(name)
    regform.States.users[user_id]["hobbies"][category] = sorted(arr)
    regform.States.users[user_id]["hobbies"]["visual"] = varr

@dp.callback_query(F.data.split("*")[0] == "slider")
async def slide_control(callback: types.CallbackQuery):
    cb = callback.message.reply_markup.inline_keyboard[0][0].callback_data.split("*")
    query = callback.data.split("*")
    uid = callback.message.chat.id
    kb = InlineKeyboardMarkup(inline_keyboard=regform.get_buttons_slider(uid, query[1], cb[0] + "*" + cb[1], True, int(query[2])))
    await callback.message.edit_reply_markup(
        reply_markup=kb
    )

@dp.callback_query(F.data.split("*")[0] == "steps")
async def change_step(callback: types.CallbackQuery, state: FSMContext):
    query = callback.data.split("*")
    uid = callback.message.chat.id
    multiplier = int(query[2])
    if query[1] == "next":
        for i in range(multiplier):
            regform.States.next_step(
                message = callback.message,
                user_id = uid,
                bot = bot,
                state = state
            )
    elif query[1] == "prev":
        for i in range(multiplier):
            regform.States.prev_step(
                message = callback.message,
                user_id = uid,
                bot = bot,
                state = state
            )
    try:
        form = get_form(regform.States.current_step(uid))
    except KeyError:
        form = None
    await regform.States.toggle_from_step_name(
        uid,
        callback.message,
        form,
        bot,
        state
    )

@dp.callback_query(F.data.split("*")[0] == "search")
async def send_profile(cb: types.CallbackQuery):
    query = F.data.split("*")
    uid = cb.message.chat.id 
    if query[1] == "sim":
        await send_sim_user(uid, cb.message)

@dp.callback_query(F.data.split("*")[0] == "states")
async def states_manager(callback: types.CallbackQuery, state: FSMContext):
    query = F.data.split("*")
    uid = callback.message.chat.id
    match query:
        case "save":
            await callback.message.delete()
            #TODO Сохранение в БД информации пользователя (определить в каком виде лучше хранить информацию.)
            user: User = User(
                uid = uid,
                photo_id = regform.States.get_value_from_key(uid, "photo"),
                profile = regform.form_constructor(uid),
                jstring = ml_split_fields(regform.States.users[uid])
            )
            await profiles.add_user(user)
            await callback.message.answer(text = "Анкета сохранена.")
        case "clear":
            await callback.message.delete()
            await callback.message.answer(text = "Анкета очищена.")
@dp.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer("help")

async def onStart():
    print("Started.")

if __name__ == '__main__':
    dp.run_polling(bot, skip_updates = True)


