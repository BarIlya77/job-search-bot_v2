# src/services/filter_service.py
from typing import Dict, Any
from logger import get_logger
from src.storage.database import get_session
from src.storage.repositories.filter_repo import get_filter_repo

logger = get_logger(__name__)


class FilterService:
    """Сервис для работы с фильтрами поиска"""

    async def get_user_filters(self, user_id: int) -> Dict[str, Any]:
        """Получить фильтры пользователя"""
        async for session in get_session():
            repo = get_filter_repo(session)
            return await repo.get_user_filters(user_id)
        return {}

    async def to_hh_params(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразовать фильтры пользователя в параметры HH API"""
        params = {}

        # Текстовый запрос (профессия)
        if filters.get('profession'):
            params['text'] = filters['profession']

        # Опыт работы
        if filters.get('experience'):
            # HH API ожидает такие значения опыта
            exp_map = {
                'noExperience': 'noExperience',
                'between1And3': 'between1And3',
                'between3And6': 'between3And6',
                'moreThan6': 'moreThan6'
            }
            exp_value = exp_map.get(filters['experience'])
            if exp_value:
                params['experience'] = exp_value

        # Зарплата
        if filters.get('salary_min'):
            try:
                salary = int(filters['salary_min'])
                params['salary'] = salary
                params['only_with_salary'] = True
            except (ValueError, TypeError):
                logger.error(f"Некорректная зарплата: {filters.get('salary_min')}")

        # График работы
        if filters.get('schedule'):
            # HH API ожидает schedule значения
            schedule_map = {
                'office': 'fullDay',
                'remote': 'remote',
                'hybrid': 'flexible',
                'flexible': 'flexible'
            }
            schedule_value = schedule_map.get(filters['schedule'])
            if schedule_value:
                params['schedule'] = schedule_value

        # Город
        if filters.get('area'):
            area = filters['area']
            # Если это ID города (число в строке)
            if area.isdigit():
                params['area'] = int(area)
            # Если это "remote"
            elif area == 'remote':
                params['schedule'] = 'remote'
            # Если это название города - добавляем в текстовый поиск
            else:
                current_text = params.get('text', '')
                params['text'] = f"{current_text} {area}".strip()

        logger.info(f"Преобразованные параметры HH API: {params}")
        return params


# Глобальный экземпляр сервиса
filter_service = FilterService()