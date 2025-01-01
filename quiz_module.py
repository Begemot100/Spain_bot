import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import session, User, LearnedWord
from word_generator import generate_words_for_topic  # Функция для генерации слов

# Сохранение текущих слов пользователя
user_words = {}

# Обработчик выбора темы
async def topic_words_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем выбранную тему
    topic = query.data.split(":")[1]

    # Генерируем слова по теме
    words = await generate_words_for_topic(topic)

    if not words:
        await query.message.reply_text("Не удалось сгенерировать слова. Попробуйте снова.")
        return

    # Сохраняем слова для пользователя
    user_words[query.from_user.id] = {
        "words": words,
        "index": 0,
        "correct_answers": 0
    }

    # Показываем первое слово
    await show_word(update, query.from_user.id)

# Отображение слова
async def show_word(update, user_id):
    user_data = user_words.get(user_id)
    if not user_data:
        return

    index = user_data["index"]
    words = user_data["words"]

    if index >= len(words):
        # Все слова просмотрены, запускаем тест
        await start_quiz(update, user_id)
        return

    # Текущее слово
    word = words[index]
    keyboard = [[InlineKeyboardButton("Далее", callback_data="next_word")]]

    await update.callback_query.message.reply_text(
        f"Слово: {word.split(' - ')[0]}\nПеревод: {word.split(' - ')[1]}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    user_data["index"] += 1

# Обработчик кнопки "Далее"
async def next_word_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Отображаем следующее слово
    await show_word(update, query.from_user.id)

# Начало теста
async def start_quiz(update, user_id):
    user_data = user_words.get(user_id)
    if not user_data:
        return

    user_data["index"] = 0  # Сбрасываем индекс для теста
    await send_quiz_question(update, user_id)

# Отправка вопроса викторины
async def send_quiz_question(update, user_id):
    user_data = user_words.get(user_id)
    if not user_data:
        return

    index = user_data["index"]
    words = user_data["words"]

    if index >= len(words):
        # Тест завершен
        correct_answers = user_data["correct_answers"]
        total_questions = len(words)
        score = (correct_answers / total_questions) * 100

        if score >= 80:
            result = "✅ Тест успешно завершен! Вы ответили правильно на большинство вопросов."
        else:
            result = "❌ Тест завершен. Попробуйте пройти еще раз, изучив слова внимательнее."

        await update.callback_query.message.reply_text(result)
        return

    # Текущее слово
    word = words[index]
    original, translation = word.split(" - ")

    # Формируем варианты ответов
    all_words = [w.split(" - ")[1] for w in words]
    all_words.remove(translation)
    options = [translation] + all_words[:3]
    random.shuffle(options)

    keyboard = [
        [InlineKeyboardButton(option, callback_data=f"quiz_answer:{option}:{translation}")]
        for option in options
    ]

    await update.callback_query.message.reply_text(
        f"Как переводится слово: {original}?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    user_data["index"] += 1

# Обработчик ответа на вопрос викторины
async def quiz_answer_handler(update, context):
    query = update.callback_query
    await query.answer()

    # Получаем выбранный и правильный ответы
    _, selected, correct = query.data.split(":")

    user_data = user_words.get(query.from_user.id)
    if not user_data:
        return

    if selected == correct:
        user_data["correct_answers"] += 1
        await query.message.reply_text("✅ Правильно!")
    else:
        await query.message.reply_text(f"❌ Неправильно. Правильный ответ: {correct}")

    # Отправляем следующий вопрос
    await send_quiz_question(update, query.from_user.id)

# Подключение обработчиков
