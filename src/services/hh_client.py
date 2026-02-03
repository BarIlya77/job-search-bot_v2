import aiohttp
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from logger import get_logger

logger = get_logger(__name__)


class HHAPIClient:
    """Клиент для работы с API HeadHunter"""

    BASE_URL = "https://api.hh.ru"

    async def search_vacancies(self, **params) -> List[Dict]:
        """Поиск вакансий по параметрам"""
        # Очищаем None значения
        search_params = {k: v for k, v in params.items() if v is not None}

        # Подготовка параметров
        prepared_params = {}
        for key, value in search_params.items():
            if isinstance(value, bool):
                prepared_params[key] = str(value).lower()
            elif isinstance(value, (int, float)):
                prepared_params[key] = str(value)
            elif isinstance(value, str):
                prepared_params[key] = value
            elif value is not None:
                prepared_params[key] = str(value)

        logger.info(f"Поиск вакансий с параметрами: {json.dumps(prepared_params, ensure_ascii=False)}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.BASE_URL}/vacancies",
                        params=prepared_params,
                        headers={
                            "User-Agent": "JobSearchBot/1.0 (job-search-bot@example.com)",
                            "HH-User-Agent": "JobBot/1.0"
                        },
                        timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    response_text = await response.text()
                    logger.debug(f"Ответ API (статус {response.status}): {response_text[:500]}...")

                    if response.status == 200:
                        data = await response.json()
                        vacancies = data.get("items", [])
                        found = data.get("found", 0)
                        pages = data.get("pages", 0)

                        logger.info(f"Найдено вакансий: {found}, страниц: {pages}, возвращено: {len(vacancies)}")
                        return vacancies
                    else:
                        logger.error(f"Ошибка API {response.status}: {response_text}")
                        return []

        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при запросе к HH API: {e}")
            return []
        except asyncio.TimeoutError:
            logger.error("Таймаут при запросе к HH API")
            return []
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к HH API: {e}", exc_info=True)
            return []

    async def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """Получить детальную информацию о вакансии"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.BASE_URL}/vacancies/{vacancy_id}",
                        headers={
                            "User-Agent": "JobSearchBot/1.0",
                            "HH-User-Agent": "JobBot/1.0"
                        }
                ) as response:

                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Вакансия {vacancy_id} не найдена: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Ошибка получения вакансии {vacancy_id}: {e}")
            return None

    def _format_time_ago(self, published_at_str: str) -> str:
        """Форматирует время публикации в понятный формат"""
        try:
            # Парсим дату из формата HH API (например: "2024-01-23T14:30:00+0300")
            # Убираем возможное двоеточие в часовом поясе для совместимости
            if published_at_str[-3] == ":":
                published_at_str = published_at_str[:-3] + published_at_str[-2:]

            dt_format = "%Y-%m-%dT%H:%M:%S%z"
            published_at = datetime.strptime(published_at_str, dt_format)
            now = datetime.now(timezone.utc)

            # Приводим к одному часовому поясу (UTC) для сравнения
            published_at_utc = published_at.astimezone(timezone.utc)
            now_utc = now.astimezone(timezone.utc)

            time_diff = now_utc - published_at_utc

            # Определяем формат отображения
            if time_diff.days > 30:
                # Больше месяца - показываем дату
                return f"📅 {published_at.strftime('%d.%m.%Y')}"
            elif time_diff.days > 0:
                # Дни назад
                days = time_diff.days
                if days == 1:
                    return "🕐 1 день назад"
                elif 2 <= days <= 4:
                    return f"🕐 {days} дня назад"
                else:
                    return f"🕐 {days} дней назад"
            elif time_diff.seconds >= 3600:
                # Часы назад
                hours = time_diff.seconds // 3600
                if hours == 1:
                    return "🕐 1 час назад"
                elif 2 <= hours <= 4:
                    return f"🕐 {hours} часа назад"
                else:
                    return f"🕐 {hours} часов назад"
            elif time_diff.seconds >= 60:
                # Минуты назад
                minutes = time_diff.seconds // 60
                if minutes == 1:
                    return "🕐 1 минуту назад"
                elif 2 <= minutes <= 4:
                    return f"🕐 {minutes} минуты назад"
                else:
                    return f"🕐 {minutes} минут назад"
            else:
                return "🕐 Только что"

        except Exception as e:
            logger.error(f"Ошибка форматирования времени: {e}")
            return "🕐 Недавно"

    def format_vacancy_message(self, vacancy: Dict) -> str:
        """Форматирование вакансии в читаемое сообщение"""
        title = vacancy.get('name', 'Без названия')
        employer = vacancy.get('employer', {}).get('name', 'Не указано')
        salary = vacancy.get('salary')
        area = vacancy.get('area', {}).get('name', 'Не указано')
        experience = vacancy.get('experience', {}).get('name', 'Не указан')
        url = vacancy.get('alternate_url', '')

        # Добавляем информацию о публикации
        published_at = vacancy.get('published_at')
        time_info = ""
        if published_at:
            time_info = self._format_time_ago(published_at)

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
        )

        # Добавляем информацию о времени публикации
        if time_info:
            message += f"\n{time_info}\n"

        message += f"\n🔗 [Ссылка на вакансию]({url})"

        return message


# Синглтон
hh_client = HHAPIClient()
