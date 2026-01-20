from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.storage.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    first_name = Column(String(100))
    username = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)

    filters = relationship("UserFilter", back_populates="user", cascade="all, delete-orphan")


class UserFilter(Base):
    __tablename__ = "user_filters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filter_type = Column(String(50), nullable=False)  # 'profession', 'salary_min', 'experience', etc
    filter_value = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", back_populates="filters")


class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    vacancy_id = Column(String(100), unique=True, index=True)
    title = Column(String(500))
    employer_name = Column(String(200))
    salary = Column(String(100))
    area = Column(String(100))
    experience = Column(String(100))
    schedule = Column(String(100))
    employment = Column(String(100))
    description = Column(Text)
    skills = Column(Text)
    url = Column(String(500))
    published_at = Column(DateTime)
    raw_data = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
