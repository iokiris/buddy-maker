from aiogram import types, F, Router
from aiogram.types import InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext

from math import ceil
from json import load as json_load
from itertools import islice

with open("static/files/cat_fields.json", "r", encoding="utf-8") as f:
    fields = json_load(f)


class RegisterForm:
    def __init__(self):
        self.steps = ["person", "institute", "course", "dorm_status", "hobbies_cat", 
                      "hobbies", 
                      "about_me", "photo", "finish"]
        self.users = dict()

    def get_first_step(self):
        return self.steps[0]

    def get_last_step(self):
        return self.steps[-1]

    def get_value_from_key(self, user_id: int, key):
        return self.users[user_id][key]

    def init_user_form(self, user_id: int):
        self.users[user_id] = dict()
        self.users[user_id] = {
            #"current_step": "dorm_status",
            "current_step": "person",
            "person": {
                "name": "",
                "age": 0,
                "hometown": "",
                "visual": ""
            },
            "study_info": {
                "institute": "",
                "course": 0,
                "lives_in_dorm": False,
                "visual": ""
            },
            "hobbies": {
                "last_cat": "",
                "visual": []
            },
            "about_me": "",
            "photo": "",
            "ignore_case": ["ignore_case", "visual", "last_cat"]
        }

    def current_step(self, user_id: int):
        return self.users[user_id]["current_step"]
    
    def next_step(self, message: Message, user_id: int, bot, state):
        if self.get_last_step() == self.current_step(user_id): return
        self.users[user_id]["current_step"] = self.steps[self.steps.index(self.current_step(user_id)) + 1]
        #self.toggle_button_row(self.current_step(user_id), message, user_id, bot, state)]

    def prev_step_name(self, name):
        if self.get_last_step() == name: return self.get_first_step()
        return self.steps[self.steps.index(name) - 1]

    def prev_step(self, message: Message, user_id: int, bot, state):
        if self.get_first_step() == self.current_step(user_id): return
        self.users[user_id]["current_step"] = self.steps[self.steps.index(self.current_step(user_id)) - 1]

    async def toggle_from_step_name(self, user_id, message, form, bot, state):
        stepsOrder = {
            "person": gen_personal_form,
            "institute": gen_institute_button,
            "course": gen_course_button,
            "dorm_status": is_lives_in_dorm,
            "hobbies_cat": gen_hobbies_cat_button,
            "hobbies": gen_hobbies_button,
            "photo": gen_photo_form,
            "about_me": gen_about_me_form,
            "finish": confirm_and_save_form
        }
        await stepsOrder[self.current_step(user_id)]( # Вызов функции соответствующей названию в словаре.
            user_id = user_id,
            message = message,
            form = form,
            bot = bot,
            state = state
        )


States = RegisterForm()


def get_buttons_slider(user_id: int, side: str, cb_data, is_category = False, offset: int = 0):

    buttons = []
    step = States.users[user_id]["current_step"]
    if is_category:
        d = dict_from_category(fields[step])
        cb_index = 0
        step_button = [InlineKeyboardButton(text = "Завершить этот шаг", callback_data="steps*next*2")]
    else: 
        # hobbies_cat hobbies
        prev_step = States.prev_step_name(step)
        category = States.get_value_from_key(user_id, step)["last_cat"]
        d = fields[prev_step][category]
        cb_index = 1
        step_button = [InlineKeyboardButton(text = "Вернуться к категориям", callback_data="steps*prev*1")]

    if side == "prev":
        sliced_dict = dict(islice(d.items(), max(offset, 0 + cb_index), max(offset + 4, 4)))
    elif side == "next":
        sliced_dict = dict(islice(d.items(), offset + cb_index, offset + 4 + cb_index, 1))
    else:
        sliced_dict = dict(islice(d.items(), 0 + cb_index, 0 + cb_index + 4))
    for pair in sliced_dict.items():
        #buttons.append([InlineKeyboardButton(text = pair[1], callback_data=f"add*{step}*{pair[1]}")])
        buttons.append([InlineKeyboardButton(text = pair[1][0].upper() + pair[1][1:], callback_data=f"{cb_data}*{pair[cb_index]}")])
    buttons += [
        [
            InlineKeyboardButton(text="Назад", callback_data=f"slider*prev*{max(offset-4, 0)}"), 
            InlineKeyboardButton(text="Далее", callback_data=f"slider*next*{min(offset+4, len(d))}")
        ],
        step_button
    ]
    return buttons


def parting(xs, parts):
    part_len = ceil(len(xs)/parts)
    return [xs[part_len*k:part_len*(k+1)] for k in range(parts)]

def dict_from_category(q):
    k = q.keys()
    d = dict()
    for word in k:
        d.update({
            word: q[word]["field"]
        })
    return d
async def start_form_handler(uid: int, message: Message, form, bot, state):
    #buttons = get_buttons_slider(uid, "", 4)
    #kb = types.InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=True)
    #await message.answer("Для начала необходимо заполнить анкету", reply_markup=kb)
    await form.start(bot, state)
    

def isUserRegistered(user_id: int):
    return False


async def gen_personal_form(user_id: int, message: types.Message, person_form, bot, state):
    if isUserRegistered(user_id):
        return await message.answer("У вас уже имеется заполненнная анкета.")
    else:
        States.init_user_form(user_id)
        try:
            @person_form.submit()
            async def person_form_submit_handler(form: person_form, event_chat: types.Chat):
                #States.users[user_id][States.current_step(user_id)]
                States.users[event_chat.id]["person"] = {
                    "name": form.first_name,
                    "age": form.age,
                    "hometown": form.hometown,
                    "visual": f"{form.first_name}, {form.age}. {form.hometown}"
                }

                confirm_button = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(
                    text = "Подтвердить",
                    callback_data = f"steps*next*1"
                )]])
                await form.answer(text = States.users[event_chat.id]["person"]["visual"], reply_markup=confirm_button)
        except Exception:
            None
        await start_form_handler(user_id, message, person_form, bot, state)

async def gen_photo_form(user_id: int, message: types.Message, form, bot, state):
    await message.edit_text("Отправьте своё фото для анкеты. На нем должно быть видно лицо")
    
async def gen_about_me_form(user_id: int, message: types.Message, form, bot, state):
    try:
        @form.submit()
        async def about_me_handler(form: form, event_chat: types.Chat):
            States.users[event_chat.id]["about_me"] = form.info
            confirm_button = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(
                    text = "Подтвердить",
                    callback_data = f"steps*next*1"
                )]])
            await form.answer(text = f"Ваш текст: {form.info}", reply_markup=confirm_button)
    except Exception:
        None
    await start_form_handler(user_id, message, form, bot, state)

async def gen_hobbies_cat_button(user_id: int, message: Message, form, bot, state):
    buttons = get_buttons_slider(user_id, "", "add*hobbies_cat", True, 4)
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=True)
    await message.edit_text(text="Выберите категорию хобби", reply_markup=kb)

async def gen_hobbies_button(user_id: int, message: Message, form, bot, state):
    buttons = get_buttons_slider(user_id, "", "add*hobbies", False, 4)
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=True)
    hobbies_arr = States.get_value_from_key(user_id, 'hobbies')['visual']
    if len(hobbies_arr) >= 1:
        cap = f"Выбранные хобби: {', '.join(hobbies_arr)}"
    else:
        cap = "Выберите хобби"
    await message.edit_text(text=cap, reply_markup=kb)

async def gen_institute_button(user_id: int, message: Message, form, bot, state):
    order = ["ИТКН", "ИНМиН", "ЭУПП", "ГИ", "ЭкоТех", "ИНОБР", "ИБО"]
    buttons = parting([InlineKeyboardButton(text=o, callback_data=f"set*institute*{o}") for o in order], 3)
    await message.edit_text(text = "В каком институте ты учишься?", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))

async def gen_course_button(user_id: int, message: Message, form, bot, state):
    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text = "1 курс", callback_data="set*course*1*Бакалавриат, 1 курс"), 
            InlineKeyboardButton(text = "2 курс", callback_data="set*course*2*Бакалавриат, 2 курс")
        ],
        [
            InlineKeyboardButton(text = "3 курс", callback_data="set*course*3*Бакалавриат, 3 курс"), 
            InlineKeyboardButton(text = "4 курс", callback_data="set*course*4*Бакалавриат, 4 курс")],
        [InlineKeyboardButton(text = "Магистратура", callback_data="set*course*5*Магистратура")], 
        [InlineKeyboardButton(text = "Аспирантура", callback_data="set*course*6*Аспирантура")]
    ])
    await message.edit_text(text = "На каком ты сейчас курсе?", reply_markup=buttons)

async def is_lives_in_dorm(user_id: int, message: Message, form, bot, state):
    buttons = types.InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text = "Да", callback_data="set*dorm*true*Да"), InlineKeyboardButton(text = "Нет", callback_data="set*dorm*false*Нет")
    ]])
    await message.edit_text(text = "Ты проживаешь в общежитии?", reply_markup=buttons)

def form_constructor(user_id):
    string = ""
    string += States.get_value_from_key(user_id, "person")["visual"] + '\n' # Имя, возраст и родной город.
    study_info = States.get_value_from_key(user_id, "study_info") # Словарь с информацией об институте, курсе обучения и статусе проживания в общежитии.
    courses_array = [
        "Бакалавриат, 1 курс", "Бакалавриат, 2 курс", "Бакалавриат, 3 курс", "Бакалавриат, 4 курс",
        "Магистратура",
        "Аспирантура"
        ]
    string += f"Учится в {study_info['institute']}: {courses_array[int(study_info['course']) - 1]}" + '\n'
    if study_info["lives_in_dorm"]:
        string += "Проживает в общежитии." + '\n' #TODO: добавить в каком общежитии именно проживает человек. (Найти список общежитий)
    string += "Хобби: " + ", ".join(States.get_value_from_key(user_id, "hobbies")["visual"]) + '\n'
    string += "\n" + "О себе:" + "\n"
    string += States.get_value_from_key(user_id, "about_me")
    return string

async def confirm_and_save_form(user_id: int, message: Message, form, bot, state):
    form_in_string = form_constructor(user_id)
    buttons = types.InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text = "Сохранить анкету", callback_data="states*save*сохранить")], 
        [InlineKeyboardButton(text = "Отменить заполнение", callback_data="states*clear*очистить")]]
    )
    await message.edit_caption(
        caption = "Ваша анкета: " + '\n' + form_in_string, reply_markup=buttons
    )
