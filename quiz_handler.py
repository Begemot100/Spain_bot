from sqlalchemy import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import random

from telegram.ext import CallbackContext, CallbackQueryHandler

from database import session, LearnedWord, User
from dictionary_module import save_learned_words
from word_generator import generate_words_for_topic


async def topic_words_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем выбранную тему из callback_data
    topic = query.data.split(":")[1]

    # Генерируем слова для выбранной темы
    words = await generate_words_for_topic(topic)

    # Если слова не сгенерированы, отправляем сообщение об ошибке
    if not words:
        await query.message.reply_text(f"Не удалось сгенерировать слова по теме '{topic}'. Попробуйте ещё раз.")
        return

    # Сохраняем слова для текущего пользователя в user_data
    context.user_data["current_words"] = words
    print(words)
    # Формируем текст со словами для отправки
    words_text = "\n".join(
        [f"{index + 1}. {word['word']} - {word['translation']}" for index, word in enumerate(words)]
    )
    await query.message.reply_text(f"📚 Слова по теме '{topic}':\n\n{words_text}")
    print("Текущие слова в user_data:", context.user_data.get("current_words"))

    # Добавляем кнопку "Проверь себя"
    check_yourself_keyboard = [[InlineKeyboardButton("Проверь себя", callback_data="start_quiz")]]
    await query.message.reply_text(
        "Когда будете готовы, нажмите кнопку ниже:",
        reply_markup=InlineKeyboardMarkup(check_yourself_keyboard)
    )
    print("Кнопка 'Проверь себя' отправлена!")


    # Формируем клавиатуру с кнопкой
    # check_yourself_keyboard = [[InlineKeyboardButton("Проверь себя", callback_data="start_quiz")]]
    # await query.message.reply_text(
    #     "Когда будете готовы, нажмите кнопку ниже:",
    #     reply_markup=InlineKeyboardMarkup(check_yourself_keyboard)
    # )
    # print("Кнопка 'Проверь себя' отправлена!")

async def start_quiz_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Инициализация данных для теста
    quiz_words = context.user_data.get("current_words", [])
    if not quiz_words:
        await query.message.reply_text("❌ Нет слов для теста. Сначала выберите тему и изучите слова.")
        print("[ERROR] current_words не найдены в user_data")
        return

    context.user_data["quiz_words"] = quiz_words
    context.user_data["quiz_index"] = 0
    context.user_data["correct_answers"] = 0

    print(f"[DEBUG] Тест начат. Слова: {quiz_words}")

    # Отправляем первый вопрос
    await send_next_question(update, context)


async def handle_answer(update, context):
    query = update.callback_query
    await query.answer()

    # Разбираем callback_data
    try:
        _, user_answer, correct_answer = query.data.split(":")
    except ValueError:
        await query.message.reply_text("Ошибка обработки ответа. Попробуйте снова.")
        return

    # Проверка правильности ответа
    if user_answer == correct_answer:
        context.user_data["correct_answers"] = context.user_data.get("correct_answers", 0)
        await query.message.reply_text("✅ Правильно!")
    else:
        await query.message.reply_text(f"❌ Неправильно. Правильный ответ: {correct_answer}")

    # Переход к следующему вопросу
    context.user_data["quiz_index"] = context.user_data.get("quiz_index", 0)
    await send_next_question(update, context)

async def send_next_question(update, context):
    quiz_index = context.user_data.get("quiz_index", 0)
    quiz_words = context.user_data.get("quiz_words", [])

    # Проверка завершения теста
    if quiz_index >= len(quiz_words):
        await finish_quiz(update, context)  # Вызов функции завершения теста
        return

    # Текущее слово для вопроса
    current_word = quiz_words[quiz_index]
    word = current_word["word"]
    correct_translation = current_word["translation"]

    # Генерация вариантов ответов
    all_translations = [w["translation"] for w in quiz_words if w["translation"] != correct_translation]
    options = random.sample(all_translations, k=min(3, len(all_translations))) + [correct_translation]
    random.shuffle(options)

    # Формируем кнопки для ответа
    keyboard = [
        [InlineKeyboardButton(option, callback_data=f"answer:{option}:{correct_translation}")]
        for option in options
    ]

    # Отправляем вопрос
    await update.callback_query.message.reply_text(
        f"Как переводится слово '{word}'?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Увеличиваем индекс текущего вопроса
    context.user_data["quiz_index"] = quiz_index + 1


async def finish_quiz(update: Update, context: CallbackContext):
    telegram_id = update.callback_query.from_user.id
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if user:
        user_id = user.id
        print(f"[DEBUG] User ID: {user_id}")

        # Сохранение слов
        if 'current_words' in context.user_data:
            # Сохраняем слова в базу данных
            await save_learned_words(user_id, context.user_data['current_words'], "Фрукты")
            print("[DEBUG] Слова сохранены в базу данных.")
        else:
            print("[ERROR] Нет текущих слов для сохранения.")

        # Отображение результатов и кнопок
        keyboard = [
            [InlineKeyboardButton("На главную", callback_data="main_menu")],
            [InlineKeyboardButton("Продолжить", callback_data="choose_topic")]
        ]

        await update.callback_query.message.reply_text(
            "🎉 Тест завершён! Ваши слова сохранены в словарь.\nЧто вы хотите сделать дальше?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.callback_query.message.reply_text(
            "Ошибка: пользователь не найден. Используйте /start для регистрации."
        )

async def save_learned_words(user_id, words, topic):
    for word in words:
        new_learned_word = LearnedWord(
            user_id=user_id,
            word=word["word"],
            translation=word["translation"],
            topic=topic
        )
        session.add(new_learned_word)
    session.commit()


# Обработчики кнопок "На главную" и "Продолжить"
async def handle_main_menu(update, context):
    main_keyboard = [
        [InlineKeyboardButton("📚 Словарь", callback_data="dictionary")],
        [InlineKeyboardButton("📘 Грамматика", callback_data="grammar")],
        [InlineKeyboardButton("🗂 Словарный запас", callback_data="vocabulary")]
    ]
    await update.callback_query.message.reply_text(
        "Вы в главном меню. Выберите раздел:",
        reply_markup=InlineKeyboardMarkup(main_keyboard)
    )


async def handle_choose_topic(update, context):
    # Здесь вы можете указать темы для выбора
    topics_keyboard = [
        [InlineKeyboardButton("Фрукты", callback_data="topic:фрукты")],
        [InlineKeyboardButton("Животные", callback_data="topic:животные")],
        [InlineKeyboardButton("Цвета", callback_data="topic:цвета")]
    ]
    await update.callback_query.message.reply_text(
        "Выберите тему для изучения слов:",
        reply_markup=InlineKeyboardMarkup(topics_keyboard)
    )


# Регистрация обработчиков в приложении
def register_handlers(application):
    application.add_handler(CallbackQueryHandler(handle_main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(handle_choose_topic, pattern="^choose_topic$"))
async def quiz_topic_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем выбранную тему
    topic = query.data.split(":")[1]

    # Получаем слова для теста из словаря
    topics = context.user_data.get("dictionary_topics", {})
    if topic not in topics:
        await query.message.reply_text("Слова по выбранной теме не найдены.")
        return

    quiz_words = [{"word": pair.split(" - ")[0], "translation": pair.split(" - ")[1]} for pair in topics[topic]]

    context.user_data["quiz_words"] = quiz_words
    context.user_data["quiz_index"] = 0
    context.user_data["correct_answers"] = 0

    await query.message.reply_text(f"🧠 Начинаем тест по теме '{topic}'!")
    await send_next_question(update, context)


async def test_topic_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем тему из callback_data
    topic = query.data.split(":")[1]

    # Загружаем слова по теме
    user = session.query(User).filter_by(telegram_id=query.from_user.id).first()
    words = session.query(LearnedWord).filter_by(user_id=user.id, topic=topic).all()

    if not words:
        await query.message.reply_text(f"Нет слов для темы '{topic}'.")
        return

    # Сохраняем слова в context для теста
    context.user_data['current_words'] = [{"word": word.word, "translation": word.translation} for word in words]

    # Начинаем тест
    await start_quiz_handler(update, context)

