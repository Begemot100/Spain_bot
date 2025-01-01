import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Загружаем URL базы данных
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не настроен.")

# Настройка SQLAlchemy
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Модель User
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    is_premium = Column(Boolean, default=False)
    progress = Column(String, default="")
    password = Column(String, nullable=True)
    status = Column(String, default="basic")
    learned_words = relationship("LearnedWord", back_populates="user")

# Модель LearnedWord
class LearnedWord(Base):
    __tablename__ = "learned_words"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    topic = Column(String, nullable=True)
    user = relationship("User", back_populates="learned_words")

# Создание таблиц
Base.metadata.create_all(bind=engine)
