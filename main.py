from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
#from deepface import DeepFace
from mtcnn import MTCNN

from static.files import config

from utils.ml_splitter import ml_split_fields
from utils.db_controller import DataHandler, User

profiles = DataHandler("databases/profiles.db")
profiles.add_tabble()

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
    #print(detectFace())
    file_info = await bot.get_file(message.photo[-1].file_id)
    #with NamedTemporaryFile("wb", suffix=".png") as pct:

    downloaded_file = await bot.download_file(file_info.file_path)
    img = Image.open(downloaded_file)
    import numpy as np
    detector = MTCNN()
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

    await message.answer("Привет, это бот MISIS Family")
    await message.answer("Кратко описать возможности")
    '''kb = [
        [
            types.KeyboardButton(text="Знакомства"),
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
    )'''
    await start_all_forms(uid, message, state)



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
            #print(callback.__dict__)
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
    #arr = regform.States.get_value_from_key(user_id, "hobbies") or []
    #if name not in arr: arr.append(name)
    category = regform.States.get_value_from_key(user_id, "hobbies")["last_cat"]
    try:
        arr = regform.States.users[user_id]["hobbies"]["visual"]
    except KeyError:
        arr = []
    if name not in arr:
        arr.append(name)
    regform.States.users[user_id]["hobbies"][category] = arr


@dp.callback_query(F.data.split("*")[0] == "slider")
async def slide_control(callback: types.CallbackQuery):
    cb = callback.message.reply_markup.inline_keyboard[0][0].callback_data.split("*")
    query = callback.data.split("*")
    print(query, cb)
    uid = callback.message.chat.id
    print(callback.message.reply_markup.inline_keyboard[0][0].callback_data)
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
                ml_split = ml_split_fields(regform.States.users[uid])
            )
            profiles.add_user(user)
            await callback.message.answer(text = "Анкета сохранена.")
        case "clear":
            await callback.message.delete()
            await callback.message.answer(text = "Анкета очищена.")
@dp.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer("help")

if __name__ == '__main__':
    dp.run_polling(bot)
