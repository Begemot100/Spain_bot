from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)

class LearnedWords(Base):
    __tablename__ = "learned_words"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    word = Column(String)
    user = relationship("User", back_populates="learned_words")

User.learned_words = relationship("LearnedWords", back_populates="user")
