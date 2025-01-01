import sys
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from telegram.ext import Application, CommandHandler, CallbackContext
from dictionary_module import *
from quiz_handler import *
from word_generator import generate_words_for_topic
from hashlib import sha256
from datetime import datetime, timedelta

import openai
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, CallbackContext
# from dictionary_module import dictionary_handler, learn_word, repeat_words, lesson_words_handler, vocabulary_handler,topic_words_handler, learn_word_handler, choose_topic_handler, topic_handler
from database import session, User, LearnedWord, Word

from lessons import lessons_data, generate_lesson_content, get_lesson_content
from quiz_handler import start_quiz_handler
from quiz_module import next_word_handler, quiz_answer_handler
# from word_generator import generate_words_for_topic
import subprocess
from dotenv import load_dotenv
# load_dotenv()

# Получаем переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Устанавливаем ключ OpenAI
openai_api_key = OPENAI_API_KEY

# Проверяем, что все переменные загружены
if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not DATABASE_URL:
    raise ValueError("Одна или несколько переменных окружения не загружены. Проверьте настройки Railway или .env файл.")

print("Все переменные окружения успешно загружены!")

print("Переменные окружения загружены успешно.")

# Обработчик команды /start
async def start(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if user:
        # Если пользователь зарегистрирован, запрашиваем пароль для входа
        context.user_data["awaiting_login_password"] = True
        await update.message.reply_text("Введите пароль для входа:")
    else:
        # Если пользователь не зарегистрирован, предлагаем зарегистрироваться
        context.user_data["awaiting_registration_username"] = True
        await update.message.reply_text("Вы не зарегистрированы. Введите желаемый логин для регистрации:")

async def handle_message(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    text = update.message.text

    # Регистрация пользователя
    if context.user_data.get("awaiting_registration_username"):
        context.user_data["registration_username"] = text
        context.user_data["awaiting_registration_username"] = False
        context.user_data["awaiting_registration_password"] = True
        await update.message.reply_text("Введите пароль для регистрации:")
    elif context.user_data.get("awaiting_registration_password"):
        username = context.user_data.get("registration_username")
        password_hash = sha256(text.encode()).hexdigest()  # Хэшируем пароль

        # Создаём нового пользователя
        new_user = User(username=username, telegram_id=telegram_id, password=password_hash, status="basic")
        session.add(new_user)
        session.commit()

        # Завершаем регистрацию
        context.user_data.clear()
        await update.message.reply_text("Регистрация завершена! Теперь вы можете использовать бот. Введите /start для входа.")
    # Логин пользователя
    elif context.user_data.get("awaiting_login_password"):
        password_hash = sha256(text.encode()).hexdigest()

        # Проверяем, существует ли пользователь с таким Telegram ID и паролем
        user = session.query(User).filter_by(telegram_id=telegram_id, password=password_hash).first()

        if user:
            # Успешный вход
            context.user_data.clear()
            main_keyboard = [
                [InlineKeyboardButton("📚 Словарь", callback_data="dictionary")],
                [InlineKeyboardButton("📘 Грамматика", callback_data="grammar")],
                [InlineKeyboardButton("🗂 Словарный запас", callback_data="vocabulary")]
            ]
            await update.message.reply_text(
                f"Добро пожаловать, {user.username}! Ваш профиль загружен.",
                reply_markup=InlineKeyboardMarkup(main_keyboard)
            )
        else:
            # Неверный пароль
            await update.message.reply_text("Неверный пароль. Попробуйте ещё раз:")
    else:
        # Если сообщение не связано с регистрацией или входом
        await update.message.reply_text("Введите /start для начала работы с ботом.")

async def login(update: Update, context: CallbackContext):
    await update.message.reply_text("Введите логин для входа:")
    context.user_data["awaiting_login"] = True


async def handle_login(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id
    text = update.message.text

    if context.user_data.get("awaiting_login"):
        # Проверяем логин пользователя
        context.user_data["login_username"] = text
        context.user_data["awaiting_login"] = False
        context.user_data["awaiting_login_password"] = True
        await update.message.reply_text("Введите пароль:")
    elif context.user_data.get("awaiting_login_password"):
        # Проверяем пароль пользователя
        username = context.user_data.get("login_username")
        password_hash = sha256(text.encode()).hexdigest()

        user = session.query(User).filter_by(username=username, password=password_hash).first()

        if user and user.telegram_id == telegram_id:
            # Успешный вход
            context.user_data.clear()
            main_keyboard = [
                [InlineKeyboardButton("📚 Словарь", callback_data="dictionary")],
                [InlineKeyboardButton("📘 Грамматика", callback_data="grammar")],
                [InlineKeyboardButton("🗂 Словарный запас", callback_data="vocabulary")]
            ]
            await update.message.reply_text(
                f"Добро пожаловать, {user.username}! Ваш профиль загружен.",
                reply_markup=InlineKeyboardMarkup(main_keyboard)
            )
        else:
            # Неудачный вход
            context.user_data.clear()
            await update.message.reply_text("Логин или пароль неверны. Попробуйте ещё раз, используя /login.")


# Регистрация обработчиков
def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login))


def restart(update, context):
    """Команда для перезагрузки бота."""
    update.message.reply_text("Перезагружаю бота...")
    subprocess.Popen([sys.executable, 'bot.py'])  # замените 'bot.py' на ваш скрипт
    sys.exit(0)  # Завершаем текущий процесс бота


# Обработчик команды /help
async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Команды:\n/start - Зарегистрироваться или начать\n/help - Помощь\n/profile - Личный кабинет"
    )

# Обработчик команды /profile
async def profile(update: Update, context: CallbackContext):
    telegram_id = update.message.from_user.id

    # Ищем пользователя в базе данных
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if user:
        # Получаем изученные слова для пользователя
        learned_words = session.query(LearnedWord).filter_by(user_id=user.id).all()

        if learned_words:
            # Формируем текст для отображения слов
            words_text = "\n".join([f"{word.word} - {word.translation} ({word.topic})" for word in learned_words])
            await update.message.reply_text(
                f"👤 Профиль:\n"
                f"Имя пользователя: {user.username}\n"
                f"Слов изучено: {len(learned_words)}\n\n"
                f"Ваш словарь:\n{words_text}"
            )
        else:
            # Если слов нет
            await update.message.reply_text("Ваш словарь пока пуст. Изучите слова и возвращайтесь!")
    else:
        # Если пользователь не найден
        await update.message.reply_text("Вы не зарегистрированы. Используйте /start для начала.")


# Обработчик для отправки урока
async def send_basic_lesson(update: Update, context: CallbackContext):
    lesson_key = context.user_data.get('current_lesson')
    if not lesson_key:
        await update.message.reply_text("Выберите урок перед началом.")
        return

    lesson = generate_lesson_content(lesson_key)
    if not lesson or not isinstance(lesson["content"], list):
        await update.message.reply_text("Ошибка: содержание урока недоступно.")
        return

    lesson_content = "\n".join(lesson["content"])
    await update.message.reply_text(
        f"📖 Урок: {lesson['title']}\n\n{lesson_content}\n\nКогда будете готовы, введите /quiz для теста."
    )

# Обработчик для динамичного теста
async def dynamic_quiz(update: Update, context: CallbackContext):
    lesson_key = context.user_data.get("current_lesson")
    if not lesson_key:
        await update.message.reply_text("Сначала выберите урок.")
        return

    lesson = get_lesson_content(lesson_key)
    if not lesson or "quiz" not in lesson or not isinstance(lesson["quiz"], list):
        await update.message.reply_text("Ошибка: формат вопросов недоступен или неверный.")
        return

    context.user_data["quiz_progress"] = {
        "questions": lesson["quiz"],
        "current_question": 0,
        "correct_answers": 0
    }

    await update.message.reply_text(
        f"🧠 Динамичный тест по теме: {lesson['title']}\n"
        "Я задам вам несколько вопросов. Постарайтесь ответить как можно точнее!"
    )

    await send_next_dynamic_question(update, context)

async def send_next_dynamic_question(update, context):
    quiz_progress = context.user_data.get("quiz_progress")
    if not quiz_progress:
        await update.message.reply_text("Тест не найден. Начните с /quiz.")
        return

    current_question_index = quiz_progress["current_question"]
    questions = quiz_progress["questions"]

    if current_question_index >= len(questions):
        # Завершение теста
        await update.message.reply_text(
            f"Тест завершён! ✅ Вы ответили правильно на {quiz_progress['correct_answers']} из {len(questions)} вопросов."
        )
        context.user_data.pop("quiz_progress", None)
        return

    question = questions[current_question_index]
    options = "\n".join([f"{i + 1}. {opt}" for i, opt in enumerate(question["options"])])

    # Отправляем текущий вопрос
    await update.message.reply_text(
        f"Вопрос {current_question_index + 1}: {question['question']}\n{options}"
    )

    # Увеличиваем индекс текущего вопроса
    quiz_progress["current_question"] += 1

# async def handle_answer(update: Update, context: CallbackContext):
#     query = update.callback_query
#     print(f"CallbackQuery received: {query}")
#     await query.answer()
#
#     user_answer = query.data
#     quiz_progress = context.user_data.get("quiz_progress")
#
#     if not quiz_progress:
#         await query.message.reply_text("Тест не найден. Начните с /quiz.")
#         return
#
#     current_question_index = quiz_progress["current_question"] - 1
#     current_question = quiz_progress["questions"][current_question_index]
#     correct_answer = current_question["answer"]
#
#     if user_answer == correct_answer:
#         quiz_progress["correct_answers"] += 1
#         await query.message.reply_text("✅ Правильно!")
#     else:
#         await query.message.reply_text(f"❌ Неправильно. Правильный ответ: {correct_answer}")
#
#     await send_next_dynamic_question(update, context)



async def finish_quiz(update: Update, context: CallbackContext):
    quiz_data = context.user_data.get("quiz_progress")
    correct_answers = quiz_data.get("correct_answers", 0)
    total_questions = len(quiz_data.get("questions", []))

    if total_questions == 0:
        await update.message.reply_text("Тест не содержал вопросов. Попробуйте другой урок.")
        return

    score = (correct_answers / total_questions) * 100

    response = (
        f"✅ Тест завершен! Вы правильно ответили на {correct_answers} из {total_questions} вопросов.\n"
        f"Поздравляем! Переходите к следующему уроку." if score >= 80 else
        f"❌ Тест завершен. Вы правильно ответили на {correct_answers} из {total_questions} вопросов.\n"
        f"Повторите текущий урок и попробуйте снова."
    )

    await update.message.reply_text(response)

    context.user_data["quiz_progress"] = None

# print("Lesson Quiz Data:", lesson["quiz"])

async def show_description(update: Update, context: CallbackContext):
    """Показать описание текущего урока."""
    lesson_key = context.user_data.get('current_lesson')
    if not lesson_key:
        await update.message.reply_text("Сначала выберите урок.")
        return

    lesson = lessons_data[lesson_key]
    description = lesson.get('description', 'Описание недоступно.')

    await update.message.reply_text(f"📘 Описание урока: {lesson['title']}\n\n{description}")

async def update_progress(username: str):
    """Обновить прогресс пользователя."""
    user = session.query(User).filter_by(username=username).first()
    if user:
        if user.progress is None:
            user.progress = 1
        else:
            user.progress += 1
        session.commit()

async def select_lesson(update: Update, context: CallbackContext):
    """
    Обработчик для выбора урока и отправки его содержимого.
    """
    try:
        lesson_number = int(update.message.text) - 1
        lesson_keys = list(lessons_data.keys())

        if lesson_number < 0 or lesson_number >= len(lesson_keys):
            await update.message.reply_text("Урок с таким номером не найден. Попробуйте ещё раз.")
            return

        lesson_key = lesson_keys[lesson_number]
        lesson = get_lesson_content(lesson_key)
        print(f"Текущий урок: {lesson}")

        if not lesson:
            await update.message.reply_text("Урок недоступен или его содержимое отсутствует.")
            return

        description = lesson.get("description", "Описание отсутствует.")
        content = "\n".join(lesson["content"]) if isinstance(lesson["content"], list) else lesson["content"]

        await update.message.reply_text(
            f"📖 Урок: {lesson['title']}\n\nОписание: {description}\n\n{content}\n\nКогда будете готовы, введите /quiz для теста."
        )

        # Сохраняем текущий урок в контексте пользователя
        context.user_data["current_lesson"] = lesson_key

    except ValueError:
        await update.message.reply_text("Введите корректный номер урока.")

async def send_webapp_button(update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="Открыть викторину",
            web_app=WebAppInfo(url="https://060a-185-248-85-26.ngrok-free.app/quiz_buttons.html")
        )]
    ])
    await update.message.reply_text("Нажмите на кнопку ниже, чтобы открыть викторину.", reply_markup=keyboard)


async def choose_topic_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Клавиатура с выбором тем
    keyboard = [
        [InlineKeyboardButton("Еда", callback_data="topic:еда")],
        [InlineKeyboardButton("Животные", callback_data="topic:животные")],
        [InlineKeyboardButton("Цвета", callback_data="topic:цвета")],
        [InlineKeyboardButton("Глаголы", callback_data="topic:глаголы")],
        [InlineKeyboardButton("Существительные", callback_data="topic:существительные")],
        [InlineKeyboardButton("Природа", callback_data="topic:природа")],
        [InlineKeyboardButton("Спорт", callback_data="topic:спорт")],
        [InlineKeyboardButton("Путешествия", callback_data="topic:путешествия")],
        [InlineKeyboardButton("Одежда", callback_data="topic:одежда")],
        [InlineKeyboardButton("Транспорт", callback_data="topic:транспорт")],
        [InlineKeyboardButton("Эмоции", callback_data="topic:эмоции")],
        [InlineKeyboardButton("Профессии", callback_data="topic:профессии")],
        [InlineKeyboardButton("Хобби", callback_data="topic:хобби")],
        [InlineKeyboardButton("Время", callback_data="topic:время")],
        [InlineKeyboardButton("Числа", callback_data="topic:числа")],
        [InlineKeyboardButton("Предметы дома", callback_data="topic:предметы_дома")],
        [InlineKeyboardButton("Тело человека", callback_data="topic:тело_человека")],
        [InlineKeyboardButton("География", callback_data="topic:география")],
        [InlineKeyboardButton("Музыка", callback_data="topic:музыка")],
        [InlineKeyboardButton("Фрукты и овощи", callback_data="topic:фрукты_овощи")],
    ]

    await query.message.reply_text("Выберите тему:", reply_markup=InlineKeyboardMarkup(keyboard))

async def generate_topic_words_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем выбранную тему из callback_data
    topic = query.data.split(":")[1]

    # Генерируем слова по теме
    words = await generate_words_for_topic(topic)

    if not words:
        await query.message.reply_text("Не удалось сгенерировать слова. Попробуйте ещё раз.")
        return

    # Отображаем сгенерированные слова
    words_text = "\n".join(words)
    await query.message.reply_text(
        f"📚 Слова по теме '{topic}':\n\n{words_text}"
    )


async def register_user(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    username = query.from_user.username

    # Проверяем, есть ли пользователь уже в базе данных
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        await query.message.reply_text("Вы уже зарегистрированы!")
    else:
        # Создаем нового пользователя
        new_user = User(username=username, telegram_id=telegram_id, password=None, status="basic")
        session.add(new_user)
        session.commit()
        await query.message.reply_text("Регистрация завершена! Теперь вы можете пользоваться ботом.")

# Основная функция
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("quiz", dynamic_quiz))

    # Обработчики CallbackQuery
    application.add_handler(CallbackQueryHandler(topic_words_handler, pattern="^topic:"))

    application.add_handler(CallbackQueryHandler(start_quiz_handler, pattern="^start_quiz$"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^answer:"))

    application.add_handler(CallbackQueryHandler(dictionary_handler, pattern="^dictionary$"))
    application.add_handler(CallbackQueryHandler(topic_words_handler, pattern="^topic_words:"))
    application.add_handler(CallbackQueryHandler(quiz_topic_handler, pattern="^quiz_topic:"))

    application.add_handler(CallbackQueryHandler(learn_word_handler, pattern="^learn_word:"))
    application.add_handler(CallbackQueryHandler(repeat_words, pattern="^repeat:"))
    application.add_handler(CallbackQueryHandler(vocabulary_handler, pattern="^vocabulary$"))
    application.add_handler(CallbackQueryHandler(choose_topic_handler, pattern="^choose_topic$"))
    application.add_handler(CallbackQueryHandler(topic_handler, pattern="^topic:"))
    application.add_handler(CallbackQueryHandler(next_word_handler, pattern="^next_word$"))
    application.add_handler(CallbackQueryHandler(test_topic_handler, pattern="^test_topic:"))
    application.add_handler(CallbackQueryHandler(register_user, pattern="^register$"))

    async def debug_callback_query(update, context):
        query = update.callback_query
        await query.answer()
        print(f"[DEBUG] CallbackQuery: {query.data}")

    register_handlers(application)

    # Запуск бота
    application.run_polling()


if __name__ == "__main__":
    main()
