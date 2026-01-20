import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from logger import get_logger
from config import config

logger = get_logger(__name__)

Base = declarative_base()

# Создаем асинхронный движок
engine = create_async_engine(
    config.DATABASE_URL,
    echo=True,
    future=True
)

# Создаем фабрику сессий
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Инициализация базы данных"""
    # Импортируем модели здесь, чтобы они зарегистрировались в Base.metadata
    from src.storage import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ База данных инициализирована")


async def get_session() -> AsyncSession:
    """Получение сессии базы данных"""
    async with AsyncSessionLocal() as session:
        yield session