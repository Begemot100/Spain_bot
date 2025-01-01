from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)  # Уникальный идентификатор пользователя
    telegram_id = Column(Integer, unique=True, nullable=False)  # Telegram ID
    username = Column(String, unique=True, nullable=False)  # Уникальный логин пользователя
    is_premium = Column(Boolean, default=False)  # Указание премиум-статуса
    progress = Column(String, default="")  # Прогресс пользователя (например, завершенные уроки)
    password = Column(String, nullable=True)  # Хэшированный пароль
    status = Column(String, default="basic")  # Статус пользователя (basic, premium и т.д.)

    # Связь с таблицей `learned_words`
    learned_words = relationship("LearnedWord", back_populates="user")


# Модель для изученных слов
class LearnedWord(Base):
    __tablename__ = "learned_words"

    id = Column(Integer, primary_key=True)  # Уникальный идентификатор записи
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Связь с пользователем
    word = Column(String, nullable=False)  # Изученное слово
    translation = Column(String, nullable=False)  # Перевод изученного слова
    topic = Column(String, nullable=True)  # Тема слова (например, "Фрукты", "Путешествия")

    # Связь с таблицей `users`
    user = relationship("User", back_populates="learned_words")


# Модель для всех доступных слов
class Word(Base):
    __tablename__ = 'words'

    id = Column(Integer, primary_key=True)  # Уникальный идентификатор слова
    word = Column(String, nullable=False)  # Слово
    translation = Column(String, nullable=False)  # Перевод слова
    topic = Column(String, nullable=True)  # Тема слова (например, "Еда", "Животные")
    level = Column(String, nullable=True)  # Уровень сложности слова (например, "Начальный", "Средний", "Продвинутый")
    usage_example = Column(String, nullable=True)  # Пример использования слова

# Настройка базы данных
DATABASE_URL = "sqlite:///bot.db"  # SQLite база данных в текущей папке
engine = create_engine("sqlite:////Users/germany/Desktop/mess/bot/spain_lang_bot/pythonProject/bot.db")
print(engine.url)

# Создание всех таблиц
Base.metadata.create_all(engine)

# Создание сессии для взаимодействия с базой данных
Session = sessionmaker(bind=engine)
session = Session()
