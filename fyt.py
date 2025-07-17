import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from states import RegisterStates, PhotoUpdateState, SearchStates, FilterStates
from db import init_db, save_profile, get_profile, update_photo, get_random_profile, get_unseen_profile, \
    get_profile_by_id, delete_profile, get_profiles_by_filters
from aiogram.types import CallbackQuery

TOKEN = '8061407851:AAEIM5-UBABJUvmEiOUbky2suNuurLzXmCI'

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
init_db()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="✏️ Изменить анкету")],
        [KeyboardButton(text="📷 Изменить фото"), KeyboardButton(text="👤 Моя анкета")],
        [KeyboardButton(text="🗑 Удалить анкету")]
    ],
    resize_keyboard=True
)

register_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🚫 Отмена")]],
    resize_keyboard=True
)

search_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="💤 Перерыв")]],
    resize_keyboard=True
)

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    if get_profile(message.from_user.id):
        await message.answer("Главное меню:", reply_markup=main_menu)
    else:
        await message.answer("Приветствую! Я - бот Find Your Team."
                             "\n\n❗Прежде чем продолжить, подтвердите, что вы добровольно предоставляете данные "
                             "для отображения.\n🔒 Мы не передаём ваши данные третьим лицам.\n"
                             "✅ Отправляя анкету, вы соглашаетесь с её публикацией в целях поиска напарников/команды.",
                             reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Подтверждаю")]],
                                                              resize_keyboard=True)
                             )

@dp.message(F.text == "✅ Подтверждаю")
async def confirmed_consent(message: Message, state: FSMContext):
    await message.answer("Теперь вы можете создать анкету. Напишите /register", reply_markup=ReplyKeyboardRemove())
    await state.clear()

@dp.message(F.text == "/register")
async def start_register(message: Message, state: FSMContext):
    if get_profile(message.from_user.id):
        await message.answer("Как вас зовут?", reply_markup=register_menu)
    else:
        await message.answer("Как вас зовут?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.name)

@dp.message(RegisterStates.name)
async def get_name(message: Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, введите имя текстом.")
    if message.text == "🚫 Отмена":
        return await cancel_registration(message, state)
    await state.update_data(name=message.text)
    if get_profile(message.from_user.id):
        await message.answer("Из какого вы города?\nПожалуйста, указывайте точное название города с заглавной буквы "
                             "- это поможет потенциальным напарникам быстрее найти вас!",
                             reply_markup=register_menu)
    else:
        await message.answer("Из какого вы города?\nПожалуйста, указывайте точное название города с заглавной буквы "
                             "- это поможет потенциальным напарникам быстрее найти вас!",
                             reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.city)

@dp.message(RegisterStates.city)
async def get_city(message: Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, введите город текстом.")
    if message.text == "🚫 Отмена":
        return await cancel_registration(message, state)
    await state.update_data(city=message.text)
    if get_profile(message.from_user.id):
        await message.answer("Какие у вас навыки? (через запятую)", reply_markup=register_menu)
    else:
        await message.answer("Какие у вас навыки? (через запятую)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.skills)

@dp.message(RegisterStates.skills)
async def get_skills(message: Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, укажите навыки текстом.")
    if message.text == "🚫 Отмена":
        return await cancel_registration(message, state)
    await state.update_data(skills=message.text)
    if get_profile(message.from_user.id):
        await message.answer("Кого вы ищете в команду?", reply_markup=register_menu)
    else:
        await message.answer("Кого вы ищете в команду?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.looking_for)

@dp.message(RegisterStates.looking_for)
async def get_target(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        return await cancel_registration(message, state)
    if not message.text:
        return await message.answer("Пожалуйста, укажите, кого вы ищете, текстом.")
    await state.update_data(looking_for=message.text)
    if get_profile(message.from_user.id):
        await message.answer("Сколько у вас лет опыта? (Введите цифру/число)\nПожалуйста, указывайте ваш "
                             "реальный опыт - это поможет потенциальным напарникам быстрее найти вас!",
                             reply_markup=register_menu)
    else:
        await message.answer("Сколько у вас лет опыта? (Введите цифру/число)\nПожалуйста, указывайте ваш "
                             "реальный опыт - это поможет потенциальным напарникам быстрее найти вас!",
                             reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.experience)


@dp.message(RegisterStates.experience)
async def get_experience(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        return await cancel_registration(message, state)
    if not message.text.isdigit():
        return await message.answer("Пожалуйта, введите стаж в виде цифры/числа. Например: 2")
    if int(message.text) >= 100:
        return await message.answer("Пожалуйста, введите реальный стаж!")

    try:
        exp = int(message.text)
        if exp < 0:
            raise ValueError
        await state.update_data(experience=exp)
    except ValueError:
        return await message.answer("Введите целое число лет опыта.")

    if get_profile(message.from_user.id):
        await message.answer("📷 Прикрепите фото для анкеты или напишите /skip, чтобы пропустить этот шаг.",
                             reply_markup=register_menu)
    else:
        await message.answer("📷 Прикрепите фото для анкеты или напишите /skip, чтобы пропустить этот шаг.",
                             reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.photo_id)

@dp.message(RegisterStates.photo_id, F.photo)
async def get_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    if get_profile(message.from_user.id):
        await message.answer("Напишите короткое описание или комментарий:", reply_markup=register_menu)
    else:
        await message.answer("Напишите короткое описание или комментарий:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.description)

@dp.message(RegisterStates.photo_id, F.text == "/skip")
async def skip_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=None)
    if get_profile(message.from_user.id):
        await message.answer("Напишите короткое описание или комментарий:", reply_markup=register_menu)
    else:
        await message.answer("Напишите короткое описание или комментарий:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterStates.description)

@dp.message(RegisterStates.photo_id)
async def invalid_photo_input(message: Message):
    if get_profile(message.from_user.id):
        await message.answer("Пожалуйста, отправьте фотографию или используй /skip для пропуска.",
                         reply_markup=register_menu)
    else:
        await message.answer("Пожалуйста, отправьте фотографию или используй /skip для пропуска.",
                             reply_markup=ReplyKeyboardRemove())

@dp.message(RegisterStates.photo_id, F.text == "🚫 Отмена")
async def cancel_photo_upload(message: Message, state: FSMContext):
    await cancel_registration(message, state)

@dp.message(RegisterStates.description)
async def get_description(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        return await cancel_registration(message, state)
    if not message.text:
        if get_profile(message.from_user.id):
            return await message.answer("Пожалуйста, введите описание текстом.", reply_markup=register_menu)
        else:
            return await message.answer("Пожалуйста, введите описание текстом.", reply_markup=ReplyKeyboardRemove())
    await state.update_data(description=message.text)
    data = await state.get_data()

    save_profile(
        user_id=message.from_user.id,
        name=data['name'],
        city=data['city'],
        skills=data['skills'],
        looking_for=data['looking_for'],
        experience=data['experience'],
        description=data['description'],
        photo_id=data.get('photo_id')
    )

    await message.answer("📊 Анкета сохранена!", reply_markup=main_menu)
    await state.clear()

@dp.message(F.text == "👤 Моя анкета")
async def my_profile(message: Message):
    profile = get_profile(message.from_user.id)
    if profile:
        _, name, city, skills, looking_for, experience, description, photo_id = profile
        if photo_id:
            await message.answer_photo(photo_id, caption=(
                f"<b>Имя:</b> {name}\n"
                f"<b>Город:</b> {city}\n"
                f"<b>Навыки:</b> {skills}\n"
                f"<b>Ищет:</b> {looking_for}\n"
                f"<b>Стаж (в годах):</b> {experience}\n"
                f"<b>О себе:</b> {description}"
            ))
        else:
            await message.answer(
                f"<b>Имя:</b> {name}\n"
                f"<b>Город:</b> {city}\n"
                f"<b>Навыки:</b> {skills}\n"
                f"<b>Ищет:</b> {looking_for}\n"
                f"<b>Стаж (в годах):</b> {experience}\n"
                f"<b>О себе:</b> {description}"
            )
    else:
        await message.answer("У вас ещё нет анкеты. Напишите /register")

@dp.message(F.text == "📷 Изменить фото")
async def change_photo(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        return await cancel_registration(message, state)
    await message.answer("Для отмены нажмите кнопку. \n\nОтправьте новое фото:", reply_markup=register_menu)
    await state.set_state(PhotoUpdateState.waiting_for_photo)

@dp.message(PhotoUpdateState.waiting_for_photo, F.photo)
async def update_user_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    update_photo(message.from_user.id, photo_id)
    await message.answer("📷 Фото обновлено!", reply_markup=main_menu)
    await state.clear()

@dp.message(PhotoUpdateState.waiting_for_photo)
async def invalid_update_photo(message: Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        return await cancel_registration(message, state)
    await message.answer("Пожалуйста, отправьте фотографию, чтобы обновить аватар.", reply_markup=register_menu)

@dp.message(F.text == "✏️ Изменить анкету")
async def restart_registration(message: Message, state: FSMContext):
    await message.answer("Для отмены нажмите кнопку.\n\nРедактирование анкеты:", reply_markup=register_menu)
    await start_register(message, state)

@dp.message(F.text == "🚫 Отмена")
async def cancel_registration(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Возвращение в главное меню.", reply_markup=main_menu)

@dp.message(F.text == "🔍 Поиск")
async def start_search(message: Message, state: FSMContext):
    await message.answer("Выберите режим поиска:",
                         reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔎 Все анкеты"),
                                                                     KeyboardButton(text="🎯 По фильтру")]],
                                                          resize_keyboard=True))

@dp.message(F.text == "🔎 Все анкеты")
async def search_all(message: Message, state: FSMContext):
    await state.set_state(SearchStates.active_search)
    await state.update_data(seen_ids=[])
    await message.answer("Поиск...", reply_markup=search_menu)
    await show_next_profile(message.from_user.id, message, state)

@dp.message(F.text == "🎯 По фильтру")
async def search_on_filters(message: Message, state: FSMContext):
    await state.set_state(FilterStates.choosing_filters)
    await state.update_data(filters={})
    await message.answer("Выберите нужный(-е) фильтр(-ы):",
                         reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🏢 Город"),
                                                                     KeyboardButton(text="📚 Стаж"),
                                                                    KeyboardButton(text="📷 Наличие фотографии")],
                                                                    [KeyboardButton(text="✅ Старт"),
                                                                     KeyboardButton(text="🔄 Сброс")],
                                                                     [KeyboardButton(text="💤 Перерыв")]],
                                                          resize_keyboard=True))
@dp.message(FilterStates.choosing_filters, F.text == "🏢 Город")
async def choose_city_filter(message: Message, state: FSMContext):
    await message.answer("Введите название города:")
    await state.set_state(FilterStates.filter_city)

@dp.message(FilterStates.choosing_filters, F.text == "📚 Стаж")
async def choose_experience_filter(message: Message, state: FSMContext):
    await message.answer("Введите минимальный стаж (число лет):")
    await state.set_state(FilterStates.filter_experience)

@dp.message(FilterStates.choosing_filters, F.text == "📷 Наличие фотографии")
async def choose_photo_filter(message: Message, state: FSMContext):
    await message.answer("Выберите 'Да' для поиска с фото или 'Нет' для без фото:")
    await state.set_state(FilterStates.filter_photo)

@dp.message(FilterStates.choosing_filters, F.text.in_(["✅ Старт", "Старт"]))
async def start_filtering(message: Message, state: FSMContext):
    data = await state.get_data()
    filters = data.get('filters', {})
    await start_filtered_search(message, state, filters)

@dp.message(FilterStates.choosing_filters, F.text.in_(["🔄 Сброс", "Сброс"]))
async def reset_filters(message: Message, state: FSMContext):
    await state.update_data(filters={})
    await message.answer("Фильтры сброшены. Выберите фильтр или нажмите 'Старт'.")

@dp.message(FilterStates.choosing_filters, F.text.in_(["💤 Перерыв", "Перерыв"]))
async def cancel_filtering(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("💤 Перерыв. Возвращение в главное меню.", reply_markup=main_menu)

@dp.callback_query(F.data == "skip")
async def skip_filtered_or_regular(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    filters = data.get('filters')
    if filters:
        await show_next_filtered_profile(callback.from_user.id, callback.message, state, filters)
    else:
        await show_next_profile(callback.from_user.id, callback.message, state)
    await callback.answer()

@dp.message(FilterStates.filter_city)
async def input_city(message: Message, state: FSMContext):
    city = message.text.strip()
    data = await state.get_data()
    filters = data.get('filters', {})
    filters['city'] = city
    await state.update_data(filters=filters)
    await message.answer(f"Фильтр по городу '{city}' добавлен.\nВыберите следующий фильтр или напишите 'Старт'.")
    await state.set_state(FilterStates.choosing_filters)

@dp.message(FilterStates.filter_experience)
async def input_experience(message: Message, state: FSMContext):
    try:
        exp = int(message.text.strip())
        if exp < 0:
            raise ValueError
    except ValueError:
        return await message.answer("Введите корректное неотрицательное число для стажа.")
    data = await state.get_data()
    filters = data.get('filters', {})
    filters['experience'] = exp
    await state.update_data(filters=filters)
    await message.answer(f"Фильтр по стажу от {exp} лет добавлен.\nВыберите следующий фильтр или напишите 'Старт'.")
    await state.set_state(FilterStates.choosing_filters)

@dp.message(FilterStates.filter_photo)
async def input_photo_filter(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    if text in ('да', 'yes', 'есть', 'y'):
        has_photo = True
    elif text in ('нет', 'no', 'нету', 'n'):
        has_photo = False
    else:
        return await message.answer("Введите 'Да' или 'Нет'.")
    data = await state.get_data()
    filters = data.get('filters', {})
    filters['has_photo'] = has_photo
    await state.update_data(filters=filters)
    await message.answer(f"Фильтр по наличию фотографии '{'есть' if has_photo else 'нет'}' добавлен.\nВыберите следующий фильтр или напишите 'Старт'.")
    await state.set_state(FilterStates.choosing_filters)

async def start_filtered_search(message: Message, state: FSMContext, filters: dict):
    await state.set_state(FilterStates.searching)
    await state.update_data(seen_ids=[])
    await message.answer("Начинаю поиск с выбранными фильтрами...", reply_markup=search_menu)
    curr_user_id = message.from_user.id
    filters["exclude_user_id"] = curr_user_id
    await show_next_filtered_profile(message.from_user.id, message, state, filters)

async def show_next_filtered_profile(user_id: int, message: Message, state: FSMContext, filters: dict):
    data = await state.get_data()
    seen_ids = data.get('seen_ids', [])
    last_msg_id = data.get('last_filtered_profile_msg_id')

    if last_msg_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=last_msg_id,
                reply_markup=None
            )
        except:
            pass

    exclude_ids = seen_ids + [user_id]

    profiles = get_profiles_by_filters(
        city=filters.get('city'),
        experience=filters.get('experience'),
        has_photo=filters.get('has_photo'),
        exclude_ids=exclude_ids
    )
    if not profiles:
        await message.answer("😢 Анкеты по заданным фильтрам не найдены или вы все просмотрели. "
                             "Возвращение в главное меню.", reply_markup=main_menu)
        await state.clear()
        return

    profile = profiles[0]
    seen_ids.append(profile[0])
    await state.update_data(seen_ids=seen_ids)

    _, name, city, skills, looking_for, experience, description, photo_id = profile
    caption = (
        f"<b>Имя:</b> {name}\n"
        f"<b>Город:</b> {city}\n"
        f"<b>Навыки:</b> {skills}\n"
        f"<b>Ищет:</b> {looking_for}\n"
        f"<b>Стаж (в годах):</b> {experience}\n"
        f"<b>О себе:</b> {description}"
    )

    markup = get_search_inline_keyboard(profile[0])
    if photo_id:
        sent_msg = await message.answer_photo(photo_id, caption=caption, reply_markup=markup)
    else:
        sent_msg = await message.answer(caption, reply_markup=markup)
    await state.update_data(last_filtered_profile_msg_id=sent_msg.message_id)

@dp.message(F.text == "💤 Перерыв")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Возвращение в главное меню.", reply_markup=main_menu)

async def show_next_profile(user_id: int, message: Message, state: FSMContext):
    data = await state.get_data()
    seen_ids = data.get('seen_ids', [])
    profile = get_unseen_profile(user_id, seen_ids)
    if not profile:
        await message.answer("😢 Просмотрены все анкеты. Возвращение в главное меню.", reply_markup=main_menu)
        return

    seen_ids.append(profile[0])
    await state.update_data(seen_ids=seen_ids)

    _, name, city, skills, looking_for, experience, description, photo_id = profile
    caption = (
        f"<b>Имя:</b> {name}\n"
        f"<b>Город:</b> {city}\n"
        f"<b>Навыки:</b> {skills}\n"
        f"<b>Ищет:</b> {looking_for}\n"
        f"<b>Стаж (в годах):</b> {experience}\n"
        f"<b>О себе:</b> {description}"
    )

    markup = get_search_inline_keyboard(profile[0])  # profile[0] = user_id анкеты

    previous_msg_id = data.get("last_profile_msg_id")
    if previous_msg_id:
        try:
            await bot.edit_message_reply_markup(chat_id=message.chat.id, message_id=previous_msg_id, reply_markup=None)
        except Exception as e:
            print(f"Не удалось удалить кнопки: {e}")
    if photo_id:
            sent_msg = await message.answer_photo(photo_id, caption=caption, reply_markup=markup)
    else:
        sent_msg = await message.answer(caption, reply_markup=markup)
    await state.update_data(last_profile_msg_id=sent_msg.message_id)

def get_search_inline_keyboard(profile_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤝 Запрос на сотрудничество", callback_data=f"like_{profile_id}"),
            InlineKeyboardButton(text="➡️ Следующий", callback_data="skip")
        ]
    ])

@dp.callback_query(F.data.startswith("like_"))
async def like_profile(callback: CallbackQuery, state: FSMContext):
    liked_user_id = int(callback.data.split("_")[1])
    liker_id = callback.from_user.id

    if liked_user_id == liker_id:
        await callback.answer("Нельзя выбрать себя.", show_alert=True)
        return

    liker_profile = get_profile(liker_id)
    liked_profile = get_profile_by_id(liked_user_id)

    if not liked_profile:
        await callback.answer("Анкета больше недоступна.")
        return

    try:
        # Создаем клавиатуру для получателя
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👀 Посмотреть анкету",
                                                                               callback_data=f"view_{liker_id}")]])

        # Отправляем уведомление получателю
        await bot.send_message(
            chat_id=liked_user_id,
            text=f"<b>Новый запрос на сотрудничество!</b>\n\n"
                 f"Пользователь хочет работать с вами. "
                 f"Посмотрите его анкету и примите решение:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("✅ Запрос отправлен!", show_alert=True)
    except Exception as e:
        print(f"Ошибка при отправке отклика: {e}")
        await callback.answer("Не удалось отправить отклик.", show_alert=True)

    await show_next_profile(callback.from_user.id, callback.message, state)

@dp.callback_query(F.data.startswith("view_"))
async def view_profile(callback: CallbackQuery):
    profile_id = int(callback.data.split("_")[1])
    profile = get_profile_by_id(profile_id)

    if not profile:
        await callback.answer("Анкета не найдена")
        return

    _, name, city, skills, looking_for, experience, description, photo_id = profile
    caption = (
        f"<b>Анкета пользователя:</b>\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Город:</b> {city}\n"
        f"<b>Навыки:</b> {skills}\n"
        f"<b>Ищет:</b> {looking_for}\n"
        f"<b>Стаж:</b> {experience}\n"
        f"<b>О себе:</b> {description}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Хочу сотрудничать",
                callback_data=f"confirm_{profile_id}"
            ),
            InlineKeyboardButton(
                text="❌ Не подходит",
                callback_data=f"reject_{profile_id}"
            )
        ]
    ])

    try:
        if photo_id:
            await callback.message.answer_photo(
                photo_id,
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(
                caption,
                reply_markup=keyboard
            )
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при показе анкеты: {e}")
        await callback.answer("Ошибка при загрузке анкеты")

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_match(callback: CallbackQuery):
    liker_id = int(callback.data.split("_")[1])
    confirmed_by = callback.from_user.id

    liker_profile = get_profile(liker_id)
    confirmed_profile = get_profile(confirmed_by)

    if not liker_profile or not confirmed_profile:
        await callback.answer("Анкета не найдена.", show_alert=True)
        return

    try:
        await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                            reply_markup=None)

        await bot.send_message(
            liker_id,
            f"🎉 <b>{confirmed_profile[1]}</b> тоже хочет сотрудничать с тобой!\n"
            f"Вот его профиль: @{callback.from_user.username if callback.from_user.username 
                                                        else 'Пользователь без username'}",
            parse_mode="HTML"
        )

        liker_user = await bot.get_chat(liker_id)
        await bot.send_message(
            confirmed_by,
            f"🎉 Взаимное сотрудничетсво с <b>{liker_profile[1]}</b>!\n"
            f"Вот его профиль: @{liker_user.username}",
            parse_mode="HTML"
        )
        await callback.answer("Связь установлена!", show_alert=True)
    except Exception as e:
        print(f"Ошибка при отправке подтверждения: {e}")
        await callback.answer("Не удалось связаться.", show_alert=True)


@dp.callback_query(F.data.startswith("reject_"))
async def reject_match(callback: CallbackQuery):
    partner_id = int(callback.data.split("_")[1])
    curr_user_id = callback.from_user.id

    current_profile = get_profile(curr_user_id)

    try:
        await bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None
        )
        rejecter_name = current_profile[1]

        await bot.send_message(
            partner_id,
            f"К сожалению, ваш запрос на сотрудничество с {rejecter_name} был отклонен.\n"
            "Не расстраивайтесь, продолжайте поиск!"
        )
        await callback.answer(f"Вы отклонили запрос", show_alert=True)
    except Exception as e:
        print(f"Ошибка при отклонении: {e}")
        await callback.answer("Не удалось отправить отказ", show_alert=True)

@dp.callback_query(F.data == "skip")
async def skip_profile(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await show_next_profile(callback.from_user.id, callback.message, state)

@dp.message(F.text == "🗑 Удалить анкету")
async def delete_user_profile(message: Message):
    await message.answer("Подтвердите удаление анкеты",
                         reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Подтвердить"),
                                                                    KeyboardButton(text="🚫 Отмена")]],
                                                          resize_keyboard=True))

@dp.message(F.text == "✅ Подтвердить")
async def confirmed_consent(message: Message):
    delete_profile(message.from_user.id)
    await message.answer("Ваша анкета была удалена. Для возобновления использования бота напишите /start.",
                         reply_markup=ReplyKeyboardRemove())
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
