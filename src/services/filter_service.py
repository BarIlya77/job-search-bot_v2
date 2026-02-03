from typing import Dict, Any
from logger import get_logger
from src.storage.database import get_session
from src.storage.repositories.filter_repo import get_filter_repo
from src.services.city_mapping import get_city_id  # Импортируем из отдельного файла

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
            params['search_field'] = 'name'

        # Опыт работы
        if filters.get('experience'):
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
            schedule_map = {
                'office': 'fullDay',
                'remote': 'remote',
                'hybrid': 'flexible',
                'flexible': 'flexible'
            }
            schedule_value = schedule_map.get(filters['schedule'])
            if schedule_value:
                params['schedule'] = schedule_value

        # Тип занятости
        if filters.get('employment'):
            employment_map = {
                'fullDay': 'full',
                'partDay': 'part',
                'project': 'project',
                'internship': 'probation'
            }
            employment_value = employment_map.get(filters['employment'])
            if employment_value:
                params['employment'] = employment_value

        # Город - используем функцию из отдельного файла
        if filters.get('area'):
            area = filters['area']

            if area == 'remote':
                params['schedule'] = 'remote'
            elif area.isdigit():
                params['area'] = area
            else:
                # Используем функцию из city_mapping.py
                city_id = get_city_id(area)
                if city_id:
                    params['area'] = city_id
                else:
                    current_text = params.get('text', '')
                    params['text'] = f"{current_text} {area}".strip()
                    logger.warning(f"Город '{area}' не найден в маппинге")

        # Обязательные параметры
        params.update({
            'per_page': 20,
            'page': 0,
            'order_by': 'publication_time',
        })

        logger.info(f"Преобразованные параметры HH API: {params}")
        return params


# Глобальный экземпляр сервиса
filter_service = FilterService()
