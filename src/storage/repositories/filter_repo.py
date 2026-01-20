from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from src.storage.models import UserFilter
from logger import get_logger

logger = get_logger(__name__)


class FilterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_filters(self, user_id: int) -> dict:
        """Получить все фильтры пользователя в виде словаря"""
        stmt = select(UserFilter).where(UserFilter.user_id == user_id)
        result = await self.session.execute(stmt)
        filters = result.scalars().all()

        filters_dict = {}
        for f in filters:
            filters_dict[f.filter_type] = f.filter_value

        return filters_dict

    async def save_filter(self, user_id: int, filter_type: str, filter_value: str) -> None:
        """Сохранить или обновить фильтр пользователя"""
        # Получаем текущее время
        current_time = datetime.utcnow()

        # Проверяем, существует ли уже такой фильтр
        stmt = select(UserFilter).where(
            (UserFilter.user_id == user_id) &
            (UserFilter.filter_type == filter_type)
        )
        result = await self.session.execute(stmt)
        existing_filter = result.scalar_one_or_none()

        if existing_filter:
            # Обновляем существующий фильтр
            existing_filter.filter_value = filter_value
            existing_filter.updated_at = current_time
            logger.info(f"Обновлен фильтр {filter_type}={filter_value} для пользователя {user_id}")
        else:
            # Создаем новый фильтр
            new_filter = UserFilter(
                user_id=user_id,
                filter_type=filter_type,
                filter_value=filter_value,
                created_at=current_time,
                updated_at=current_time
            )
            self.session.add(new_filter)
            logger.info(f"Создан фильтр {filter_type}={filter_value} для пользователя {user_id}")

        await self.session.commit()

    async def delete_filter(self, user_id: int, filter_type: str) -> None:
        """Удалить конкретный фильтр пользователя"""
        stmt = delete(UserFilter).where(
            (UserFilter.user_id == user_id) &
            (UserFilter.filter_type == filter_type)
        )
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Удален фильтр {filter_type} для пользователя {user_id}")

    async def clear_all_filters(self, user_id: int) -> None:
        """Очистить все фильтры пользователя"""
        stmt = delete(UserFilter).where(UserFilter.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()
        logger.info(f"Очищены все фильтры для пользователя {user_id}")


# Создаем глобальный экземпляр (будем использовать с фабрикой сессий)
filter_repo = None


def get_filter_repo(session: AsyncSession) -> FilterRepository:
    """Фабрика для получения репозитория фильтров"""
    return FilterRepository(session)
