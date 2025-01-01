# Файл для хранения уроков и тестов
import os

import openai
from typing import Callable

from dotenv import load_dotenv

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Устанавливаем ключ OpenAI
openai.api_key = OPENAI_API_KEY

# Проверяем, что все переменные загружены
if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not DATABASE_URL:
    raise ValueError("Одна или несколько переменных окружения не загружены. Проверьте настройки Railway.")

print("Переменные окружения загружены успешно.")

# Токен бота
async def generate_lesson_content(prompt):
    """
    Асинхронно генерирует содержание урока с помощью GPT.
    """
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Вы преподаватель испанского языка."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        content = response["choices"][0]["message"]["content"].strip()
        return content.split("\n")  # Возвращаем как список строк
    except Exception as e:
        print(f"Ошибка при запросе OpenAI: {e}")
        return ["Ошибка при генерации контента."]

def lazy_generate_food_lesson():
    """
    Возвращает список с фразами для урока 'Еда'.
    """
    return [
        "Manzana - Яблоко",
        "Naranja - Апельсин",
        "Pera - Груша",
        "Plátano - Банан",
        "Fresa - Клубника"
    ]


lessons_data = {
    "greetings": {
    "title": "Приветствия",
    "content": [
        "¡Hola! - Привет",
        "Buenos días - Доброе утро",
        "Buenas tardes - Добрый день",
        "Buenas noches - Доброй ночи",
        "¿Cómo estás? - Как дела?",
        "Estoy bien, gracias. - У меня всё хорошо, спасибо.",
        "¿Y tú? - А у тебя?",
        "Hasta luego - До свидания",
        "Adiós - Пока",
        "Nos vemos - Увидимся"
    ],
    "description": "Добро пожаловать в изучение испанского языка!",
    "quiz": [
        {
            "question": "Как будет 'Привет' на испанском?",
            "options": ["¡Hola!", "Adiós", "Nos vemos"],
            "answer": "¡Hola!"
        },
        {
            "question": "Как будет 'Доброе утро' на испанском?",
            "options": ["Buenas noches", "Buenos días", "Buenas tardes"],
            "answer": "Buenos días"
        },
        {
            "question": "Как будет 'Добрый день' на испанском?",
            "options": ["Buenas noches", "Buenas tardes", "Buenos días"],
            "answer": "Buenas tardes"
        },
        {
            "question": "Как будет 'Доброй ночи' на испанском?",
            "options": ["Buenas tardes", "Buenas noches", "Buenos días"],
            "answer": "Buenas noches"
        },
        {
            "question": "Как сказать 'Как дела?' на испанском?",
            "options": ["¿Cómo estás?", "Estoy bien, gracias.", "¿Y tú?"],
            "answer": "¿Cómo estás?"
        },
        {
            "question": "Как сказать 'У меня всё хорошо, спасибо' на испанском?",
            "options": ["Estoy bien, gracias.", "Hasta luego", "Nos vemos"],
            "answer": "Estoy bien, gracias."
        },
        {
            "question": "Как сказать 'А у тебя?' на испанском?",
            "options": ["Adiós", "¿Y tú?", "Hasta luego"],
            "answer": "¿Y tú?"
        },
        {
            "question": "Как будет 'До свидания' на испанском?",
            "options": ["Hasta luego", "Nos vemos", "Adiós"],
            "answer": "Hasta luego"
        },
        {
            "question": "Как будет 'Пока' на испанском?",
            "options": ["Adiós", "Hasta luego", "¿Y tú?"],
            "answer": "Adiós"
        },
        {
            "question": "Как будет 'Увидимся' на испанском?",
            "options": ["Adiós", "Nos vemos", "Buenas noches"],
            "answer": "Nos vemos"
        }
    ]



    },
    "numbers": {
    "title": "Числа",
    "content": ["Uno - Один", "Dos - Два", "Tres - Три", "Cuatro - Четыре", "Cinco - Пять"],
    "description": (
        "В этом уроке вы выучите базовые числительные на испанском языке. Эти числа часто используются в повседневной "
        "жизни, например, при указании количества или времени. Изучите их, чтобы уметь считать и выражать простые "
        "цифры на испанском."
    ),
    "quiz": [
        {
            "question": "Как переводится 'Один' на испанский?",
            "options": ["Uno", "Dos", "Tres"],
            "answer": "Uno"
        },
        {
            "question": "Как переводится 'Два' на испанский?",
            "options": ["Tres", "Dos", "Cuatro"],
            "answer": "Dos"
        },
        {
            "question": "Как переводится 'Три' на испанский?",
            "options": ["Cuatro", "Cinco", "Tres"],
            "answer": "Tres"
        },
        {
            "question": "Как переводится 'Четыре' на испанский?",
            "options": ["Cuatro", "Cinco", "Dos"],
            "answer": "Cuatro"
        },
        {
            "question": "Как переводится 'Пять' на испанский?",
            "options": ["Uno", "Cinco", "Tres"],
            "answer": "Cinco"
        }
    ]


    },
    "food_dynamic": {
    "title": "Еда (Динамический)",
    "content": lazy_generate_food_lesson(),  # Убедитесь, что это список или функция, возвращающая список
    "description": "Этот урок был создан с использованием искусственного интеллекта. Вы узнаете полезные слова и фразы на тему еды.",
    "quiz": [
        {
            "question": "Как будет 'Яблоко' на испанском?",
            "options": ["Manzana", "Naranja", "Pera"],
            "answer": "Manzana"
        },
        {
            "question": "Как будет 'Апельсин' на испанском?",
            "options": ["Plátano", "Fresa", "Naranja"],
            "answer": "Naranja"
        },
        {
            "question": "Как будет 'Банан' на испанском?",
            "options": ["Plátano", "Manzana", "Pera"],
            "answer": "Plátano"
        }
    ]
}

}

print(lazy_generate_food_lesson())


def get_lesson_content(lesson_key):
    """
    Возвращает содержимое урока. Для ленивых уроков вызывает генерацию.
    """
    lesson = lessons_data.get(lesson_key)
    if not lesson:
        return None

    # Если content является функцией, вызовите её
    if callable(lesson["content"]):
        lesson["content"] = lesson["content"]()

    if not isinstance(lesson["content"], list):
        raise TypeError(f"Урок '{lesson_key}' содержит некорректный content: {lesson['content']}")

    return lesson


def validate_quiz_format(lesson_key):
    lesson = lessons_data.get(lesson_key)
    if not lesson:
        print(f"Урок с ключом '{lesson_key}' не найден.")
        return False

    quiz = lesson.get("quiz", [])
    for idx, question in enumerate(quiz, start=1):
        if not isinstance(question, dict):
            print(f"Ошибка в вопросе {idx} урока '{lesson_key}': вопрос не является словарём. Получено: {question}")
            return False
        if not all(k in question for k in ("question", "options", "answer")):
            print(f"Ошибка в вопросе {idx} урока '{lesson_key}': отсутствуют ключи 'question', 'options' или 'answer'. Получено: {question}")
            return False
        if not isinstance(question["options"], list):
            print(f"Ошибка в вопросе {idx} урока '{lesson_key}': 'options' должен быть списком. Получено: {question['options']}")
            return False
        if question["answer"] not in question["options"]:
            print(f"Ошибка в вопросе {idx} урока '{lesson_key}': 'answer' ({question['answer']}) не найден в 'options'. Получено: {question['options']}")
            return False
    print(f"Урок '{lesson_key}': все вопросы имеют корректный формат.")
    return True


# Пример использования:
validate_quiz_format("greetings")
validate_quiz_format("numbers")
validate_quiz_format("food_dynamic")

quiz_questions = []

print("Уроки успешно обновлены.")
