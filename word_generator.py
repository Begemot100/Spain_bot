import openai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
import os
from dotenv import load_dotenv

dotenv_path = "/Users/germany/Desktop/mess/bot/spain_lang_bot/pythonProject/spanish_bot/.env"
load_dotenv(dotenv_path=dotenv_path)

# Получаем переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Убедимся, что переменные загружены
if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not DATABASE_URL:
    raise ValueError("Одна или несколько переменных окружения не загружены. Проверьте файл .env.")

print("TELEGRAM_TOKEN:", TELEGRAM_TOKEN)
print("OPENAI_API_KEY:", OPENAI_API_KEY)
print("DATABASE_URL:", DATABASE_URL)

async def generate_words_for_topic(topic):
    try:
        # Отправляем запрос в OpenAI для генерации слов
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Вы учитель испанского языка."},
                {"role": "user",
                 "content": f"Сгенерируйте 10 испанских слов на тему '{topic}' с переводом на русский в формате 'слово - перевод'."}
            ]
        )

        # Получаем текст ответа
        words = response['choices'][0]['message']['content']
        print(f"[DEBUG] Ответ от OpenAI: {words}")  # Отладочный вывод

        # Разбираем текст в список слов
        parsed_words = []
        for pair in words.strip().split("\n"):
            if " - " in pair:
                try:
                    word, translation = pair.split(" - ")
                    parsed_words.append({"word": word.strip(), "translation": translation.strip()})
                except ValueError as ve:
                    print(f"[WARNING] Ошибка разбора пары: {pair}, ошибка: {ve}")
            else:
                print(f"[WARNING] Строка не соответствует формату: {pair}")

        # Проверяем результат
        if not parsed_words:
            print("[ERROR] Список слов пуст. Проверьте формат ответа от OpenAI.")
        else:
            print(f"[DEBUG] Список сгенерированных слов: {parsed_words}")

        return parsed_words
    except Exception as e:
        print(f"[ERROR] Ошибка при генерации слов: {e}")
        return []

# Пример вызова
# async def handle_topic_words(update, context):
#     query = update.callback_query
#     query.answer()
#
#     # Получаем тему из callback_data
#     topic = query.data.split(":")[1]
#
#     # Генерируем слова для выбранной темы (синхронный вызов)
#     words = generate_words_for_topic(topic)
#
#     if not words:
#         query.message.reply_text("Не удалось сгенерировать слова для этой темы. Попробуйте снова.")
#         return
#
#     # Формируем кнопки для изучения слов
#     keyboard = [
#         [InlineKeyboardButton(word, callback_data=f"learn:{word}")]
#         for word in words
#     ]
#
#     query.message.reply_text(
#         f"Слова по теме '{topic}':", reply_markup=InlineKeyboardMarkup(keyboard)
#     )