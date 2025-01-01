from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import session, User, LearnedWord, Word
from lessons import lessons_data, get_lesson_content
from word_generator import generate_words_for_topic

# Пример слов для изучения
words = [
    {"word": "Hola", "translation": "Привет"},
    {"word": "Adiós", "translation": "Пока"},
    {"word": "Gracias", "translation": "Спасибо"},
    {"word": "Por favor", "translation": "Пожалуйста"},
]

async def dictionary_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем пользователя
    user = session.query(User).filter_by(telegram_id=query.from_user.id).first()
    if not user:
        await query.message.reply_text("Вы ещё не изучили ни одного слова.")
        return

    # Группируем слова по темам
    words_by_topic = session.query(LearnedWord.topic, LearnedWord.word, LearnedWord.translation).filter_by(user_id=user.id).all()

    if not words_by_topic:
        await query.message.reply_text("Ваш словарь пока пуст. Изучите слова и возвращайтесь!")
        return

    # Формируем текст для отображения
    dictionary_text = ""
    current_topic = None
    for word in words_by_topic:
        if word.topic != current_topic:
            current_topic = word.topic
            dictionary_text += f"\n📘 Тема: {current_topic}\n"
        dictionary_text += f" - {word.word} - {word.translation}\n"

    await query.message.reply_text(f"Ваш словарь:\n{dictionary_text}")

# Обработчик для изучения слова
async def learn_word(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем слово и перевод из callback_data
    word_data = query.data.split(":")[1]
    word, translation = word_data.split(" - ")

    # Сохраняем слово как изученное
    user = session.query(User).filter_by(telegram_id=query.from_user.id).first()
    if user:
        learned_word = LearnedWord(user_id=user.id, word=word, translation=translation)
        session.add(learned_word)
        session.commit()

    await query.message.reply_text(f"Слово: {word}\nПеревод: {translation}\nДобавлено в ваш словарный запас!")


# Обработчик для "Словарного запаса"
async def vocabulary_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем изученные слова
    user = session.query(User).filter_by(telegram_id=query.from_user.id).first()
    learned_words = session.query(LearnedWord).filter_by(user_id=user.id).all()

    keyboard = []

    if learned_words:
        keyboard.extend([
            [InlineKeyboardButton(f"{word.word} - {word.translation}", callback_data=f"repeat:{word.id}")]
            for word in learned_words
        ])

    # Добавляем кнопку "Выбрать тему"
    keyboard.append([InlineKeyboardButton("🎯 Выбрать тему", callback_data="choose_topic")])

    if learned_words:
        await query.message.reply_text(
            "Ваш словарный запас:", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.message.reply_text(
            "Ваш словарный запас пуст. Вы можете выбрать тему для изучения слов.", reply_markup=InlineKeyboardMarkup(keyboard)
        )



# Обработчик для повторения слова
async def repeat_words(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем ID изученного слова
    word_id = int(query.data.split(":")[1])
    learned_word = session.query(LearnedWord).filter_by(id=word_id).first()

    if not learned_word:
        await query.message.reply_text("Слово не найдено.")
        return

    await query.message.reply_text(
        f"Слово: {learned_word.word}\nПеревод: {learned_word.translation}"
    )


# Обработчик команды /help
async def help_command(update, context):
    await update.message.reply_text(
        "Команды:\n"
        "/start - Перезапустить бота\n"
        "/profile - Профиль пользователя\n"
        "/help - Помощь\n\n"
        "Используйте меню для выбора разделов: Словарь, Грамматика, Словарный запас."
    )

# Обработчик для слов из выбранного урока
async def lesson_words_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем ключ урока
    lesson_key = query.data.split(":")[1]
    lesson = get_lesson_content(lesson_key)

    if not lesson:
        await query.message.reply_text("Урок не найден.")
        return

    # Формируем список слов из урока
    words = lesson.get("content", [])
    if not words:
        await query.message.reply_text("В этом уроке нет слов для изучения.")
        return

    # Формируем кнопки для выбора слова
    keyboard = [
        [InlineKeyboardButton(f"{word.split(' - ')[0]}", callback_data=f"learn_word:{word}")]
        for word in words
    ]

    await query.message.reply_text(
        f"📚 Слова из урока '{lesson['title']}':",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обработчик для изучения выбранного слова
async def learn_word_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем слово из callback_data
    word_data = query.data.split(":")[1]
    word, translation = word_data.split(" - ")

    # Сохраняем слово как изученное
    user = session.query(User).filter_by(telegram_id=query.from_user.id).first()
    if user:
        learned_word = LearnedWord(user_id=user.id, word=word, translation=translation)
        session.add(learned_word)
        session.commit()

    await query.message.reply_text(f"Слово: {word}\nПеревод: {translation}\nДобавлено в ваш словарный запас!")

topics = [
    "Приветствия",
    "Числа",
    "Еда",
    "Путешествия",
    "Семья",
    "Работа",
    "Погода",
    "Магазин",
    "Время",
    "Хобби"
]
async def vocabulary_lessons_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Формируем кнопки для 10 тем
    keyboard = [
        [InlineKeyboardButton(topic, callback_data=f"topic:{index}")]
        for index, topic in enumerate(topics)
    ]

    await query.message.reply_text(
        "Выберите тему для изучения:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


example_words = {
    0: ["Hola - Привет", "Adiós - Пока", "Gracias - Спасибо"],
    1: ["Uno - Один", "Dos - Два", "Tres - Три"],
    2: ["Manzana - Яблоко", "Naranja - Апельсин", "Plátano - Банан"],
    3: ["Aeropuerto - Аэропорт", "Hotel - Отель", "Pasaporte - Паспорт"],
    4: ["Madre - Мать", "Padre - Отец", "Hermano - Брат"],
    5: ["Oficina - Офис", "Jefe - Начальник", "Trabajo - Работа"],
    6: ["Sol - Солнце", "Lluvia - Дождь", "Viento - Ветер"],
    7: ["Pan - Хлеб", "Leche - Молоко", "Carne - Мясо"],
    8: ["Hora - Час", "Minuto - Минута", "Segundo - Секунда"],
    9: ["Leer - Читать", "Correr - Бегать", "Pintar - Рисовать"]
}
async def topic_words_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем выбранную тему
    topic = query.data.split(":")[1]

    # Сохраняем слова для текущего пользователя
    # context.user_data["current_words"] = [
    #     {"word": "tiempo", "translation": "время"},
    #     {"word": "hora", "translation": "час"},
    #     {"word": "minuto", "translation": "минута"},
    #     {"word": "segundo", "translation": "секунда"},
    #     {"word": "mañana", "translation": "утро"},
    #     {"word": "tarde", "translation": "вечер"},
    #     {"word": "noche", "translation": "ночь"},
    #     {"word": "semana", "translation": "неделя"},
    #     {"word": "mes", "translation": "месяц"},
    #     {"word": "año", "translation": "год"},
    # ]
    # print(f"Текущие слова в user_data: {context.user_data['current_words']}")

    # Формируем список слов и отправляем текст
    words_text = "\n".join(
        [f"{index + 1}. {word['word']} - {word['translation']}" for index, word in enumerate(context.user_data["current_words"])]
    )
    await query.message.reply_text(f"📚 Слова по теме '{topic}':\n\n{words_text}")

    # Добавляем отладку для кнопки "Проверь себя"
    print("Отправляем кнопку 'Проверь себя'...")

    # Формируем клавиатуру с кнопкой
    check_yourself_keyboard = [[InlineKeyboardButton("Проверь себя", callback_data="start_quiz")]]
    await query.message.reply_text(
        "Когда будете готовы, нажмите кнопку ниже:",
        reply_markup=InlineKeyboardMarkup(check_yourself_keyboard)
    )
    print("Кнопка 'Проверь себя' отправлена!")
    print("Текущие слова в user_data:", context.user_data.get("current_words"))

async def choose_topic_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Список доступных тем
    topics = [
        "Еда", "Животные", "Цвета", "Числа", "Природа",
        "Транспорт", "Спорт", "Одежда", "Эмоции", "Работа"
    ]

    # Формируем кнопки с темами
    keyboard = [
        [InlineKeyboardButton(topic, callback_data=f"topic:{topic.lower()}")]
        for topic in topics
    ]

    await query.message.reply_text(
        "Выберите тему для изучения:", reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def topic_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем выбранную тему из callback_data
    topic = query.data.split(":")[1]

    # Генерируем слова для выбранной темы с помощью OpenAI
    words = await generate_words_for_topic(topic)

    # Если OpenAI вернул пустой результат, отправляем сообщение об ошибке
    if not words:
        await query.message.reply_text(f"Не удалось сгенерировать слова по теме '{topic}'. Попробуйте ещё раз.")
        return

    # Сохраняем сгенерированные слова в user_data
    context.user_data["current_words"] = words

    # Формируем список слов для отправки
    words_text = "\n".join([f"{index + 1}. {word['word']} - {word['translation']}" for index, word in enumerate(words)])
    await query.message.reply_text(f"📚 Слова по теме '{topic}':\n\n{words_text}")

    # Кнопка "Проверь себя"
    check_yourself_keyboard = [[InlineKeyboardButton("Проверь себя", callback_data="start_quiz")]]
    await query.message.reply_text(
        "Когда будете готовы, нажмите кнопку ниже:",
        reply_markup=InlineKeyboardMarkup(check_yourself_keyboard)
    )


    # check_yourself_keyboard = [[InlineKeyboardButton("Проверь себя", callback_data="start_quiz")]]
    # await query.message.reply_text(
    #     "Когда будете готовы, нажмите кнопку ниже:",
    #     reply_markup=InlineKeyboardMarkup(check_yourself_keyboard)
    # )
    #
    # print("Кнопка 'Проверь себя' отправлена!")
async def save_learned_words(user_id, words, topic):
    try:
        print(f"[DEBUG] Сохраняем слова: {words} для пользователя {user_id} с темой {topic}")
        for word in words:
            learned_word = LearnedWord(
                user_id=user_id,
                word=word['word'],
                translation=word['translation'],
                topic=topic
            )
            session.add(learned_word)
        session.commit()
        print("[DEBUG] Слова успешно сохранены.")
    except Exception as e:
        print(f"[ERROR] Ошибка при сохранении слов: {e}")
        session.rollback()

