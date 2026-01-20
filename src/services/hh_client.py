# src/services/hh_client.py (основываемся на вашей рабочей версии)
import aiohttp
from typing import Dict, List, Optional
from logger import get_logger

logger = get_logger(__name__)


class HHAPIClient:
    """Клиент для работы с API HeadHunter"""

    BASE_URL = "https://api.hh.ru"

    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _prepare_params(self, params: Dict) -> Dict:
        """Подготовка параметров - преобразование типов для HH API"""
        prepared = {}

        for key, value in params.items():
            if value is None:
                continue

            # Преобразуем булевы значения в строки
            if isinstance(value, bool):
                prepared[key] = str(value).lower()
            # Преобразуем числа в строки (кроме area)
            elif isinstance(value, (int, float)) and key != 'area':
                prepared[key] = str(value)
            # Для area оставляем как есть
            elif key == 'area' and isinstance(value, (int, str)):
                prepared[key] = str(value)
            # Для строк оставляем как есть
            elif isinstance(value, str):
                prepared[key] = value
            # Для остальных типов преобразуем в строку
            else:
                prepared[key] = str(value)

        return prepared

    async def search_vacancies(self, **params) -> List[Dict]:
        """Поиск вакансий по параметрам"""
        # Стандартные параметры
        default_params = {
            "area": 1,  # Москва по умолчанию
            "per_page": 10,  # Количество результатов
            "page": 0,  # Страница
            "order_by": "publication_time",
            "search_field": "name",  # Искать в названии
        }

        # Обновляем параметры
        default_params.update(params)

        # Очищаем None и преобразуем типы
        search_params = {k: v for k, v in default_params.items() if v is not None}
        search_params = self._prepare_params(search_params)

        # Убираем параметры, которые могут вызвать ошибки
        if 'search_field' in search_params and not search_params.get('text'):
            del search_params['search_field']

        logger.info(f"Поиск вакансий с параметрами: {search_params}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.BASE_URL}/vacancies",
                        params=search_params,
                        headers={"User-Agent": "JobSearchBot/1.0"}
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        vacancies = data.get("items", [])
                        logger.info(f"Найдено вакансий: {len(vacancies)}")
                        return vacancies
                    else:
                        logger.error(f"Ошибка API: {response.status}, текст: {await response.text()}")
                        return []

        except Exception as e:
            logger.error(f"Ошибка запроса к API: {e}", exc_info=True)
            return []

    async def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """Получить детальную информацию о вакансии"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.BASE_URL}/vacancies/{vacancy_id}",
                        headers={"User-Agent": "JobSearchBot/1.0"}
                ) as response:

                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Вакансия {vacancy_id} не найдена: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Ошибка получения вакансии {vacancy_id}: {e}")
            return None

    def format_vacancy_message(self, vacancy: Dict) -> str:
        """Форматирование вакансии в читаемое сообщение"""
        title = vacancy.get('name', 'Без названия')
        employer = vacancy.get('employer', {}).get('name', 'Не указано')
        salary = vacancy.get('salary')
        area = vacancy.get('area', {}).get('name', 'Не указано')
        experience = vacancy.get('experience', {}).get('name', 'Не указан')
        url = vacancy.get('alternate_url', '')

        # Форматируем зарплату
        salary_text = "не указана"
        if salary:
            salary_from = salary.get('from')
            salary_to = salary.get('to')
            currency = salary.get('currency', 'RUR')

            if salary_from and salary_to:
                salary_text = f"{salary_from:,} - {salary_to:,} {currency}".replace(',', ' ')
            elif salary_from:
                salary_text = f"от {salary_from:,} {currency}".replace(',', ' ')
            elif salary_to:
                salary_text = f"до {salary_to:,} {currency}".replace(',', ' ')

        # Формируем сообщение
        message = (
            f"💼 *{title}*\n\n"
            f"🏢 *Компания:* {employer}\n"
            f"💰 *Зарплата:* {salary_text}\n"
            f"📍 *Местоположение:* {area}\n"
            f"📊 *Опыт:* {experience}\n"
            f"🔗 [Ссылка на вакансию]({url})"
        )

        return message


# Синглтон
hh_client = HHAPIClient()
