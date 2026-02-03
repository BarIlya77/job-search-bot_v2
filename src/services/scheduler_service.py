import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Set
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from logger import get_logger
from src.storage.database import AsyncSessionLocal
from src.storage.models import User, UserFilter
from src.services.hh_client import hh_client
from src.services.filter_service import filter_service
from src.storage.repositories.filter_repo import FilterRepository

logger = get_logger(__name__)


class SchedulerService:
    """Сервис для автоматического поиска вакансий по расписанию"""

    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.check_interval = 60  # минут по умолчанию
        self.processed_vacancies: Dict[int, Set[str]] = {}  # user_id -> set(vacancy_ids)

    async def start(self, interval_minutes: int = 60):
        """Запуск планировщика"""
        self.check_interval = interval_minutes

        # Загружаем уже обработанные вакансии для каждого пользователя
        await self._load_processed_vacancies()

        # Добавляем задачу
        trigger = IntervalTrigger(minutes=interval_minutes)
        self.scheduler.add_job(
            self.check_new_vacancies_for_all_users,
            trigger,
            id='auto_search',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"✅ Планировщик запущен. Интервал проверки: {interval_minutes} минут")

        # Сразу делаем первую проверку
        asyncio.create_task(self.check_new_vacancies_for_all_users())

    async def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown(wait=False)
        logger.info("🛑 Планировщик остановлен")

    async def _load_processed_vacancies(self):
        """Загрузка уже обработанных вакансий"""
        async with AsyncSessionLocal() as session:
            # Получаем всех пользователей
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()

            for user in users:
                self.processed_vacancies[user.id] = set()

            logger.info(f"📊 Загружено {len(users)} пользователей для автоматического поиска")

    async def check_new_vacancies_for_all_users(self):
        """Проверка новых вакансий для всех активных пользователей"""
        logger.info("🔍 Запуск автоматической проверки вакансий...")

        async with AsyncSessionLocal() as session:
            # Получаем всех активных пользователей
            stmt = select(User).where(User.is_active == True)
            result = await session.execute(stmt)
            users = result.scalars().all()

            logger.info(f"👥 Найдено {len(users)} активных пользователей")

            for user in users:
                try:
                    await self.check_new_vacancies_for_user(session, user)
                    # Небольшая задержка между пользователями
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке вакансий для пользователя {user.id}: {e}")

    async def check_new_vacancies_for_user(self, session, user: User):
        """Проверка новых вакансий для конкретного пользователя"""
        # Получаем фильтры пользователя
        repo = FilterRepository(session)
        filters = await repo.get_user_filters(user.id)

        if not filters:
            logger.debug(f"Пользователь {user.id} не имеет настроенных фильтров, пропускаем")
            return

        # Преобразуем фильтры в параметры HH API
        params = await filter_service.to_hh_params(filters)

        # Для автоматического поиска ищем только самые свежие вакансии
        # Ищем за последние 24 часа
        from_date = datetime.now() - timedelta(hours=24)
        params['date_from'] = from_date.strftime('%Y-%m-%d')
        params['order_by'] = 'publication_time'
        params['per_page'] = 10  # Ограничиваем количество для уведомлений

        logger.info(f"🔎 Автопоиск для пользователя {user.id} с параметрами: {params}")

        try:
            # Ищем вакансии
            vacancies = await hh_client.search_vacancies(**params)

            if not vacancies:
                logger.debug(f"Для пользователя {user.id} новых вакансий не найдено")
                return

            # Фильтруем уже отправленные вакансии
            new_vacancies = []
            user_processed = self.processed_vacancies.get(user.id, set())

            for vacancy in vacancies:
                vacancy_id = vacancy.get('id')
                if vacancy_id and vacancy_id not in user_processed:
                    new_vacancies.append(vacancy)

            if not new_vacancies:
                logger.debug(f"Для пользователя {user.id} все вакансии уже были отправлены")
                return

            # Отправляем уведомления о новых вакансиях
            await self.send_vacancy_notifications(user.telegram_id, new_vacancies)

            # Сохраняем ID отправленных вакансий
            for vacancy in new_vacancies:
                vacancy_id = vacancy.get('id')
                if vacancy_id:
                    user_processed.add(vacancy_id)

            # Обновляем список обработанных вакансий
            self.processed_vacancies[user.id] = user_processed

            logger.info(f"✅ Пользователю {user.id} отправлено {len(new_vacancies)} новых вакансий")

        except Exception as e:
            logger.error(f"Ошибка при поиске вакансий для пользователя {user.id}: {e}")

    async def send_vacancy_notifications(self, chat_id: int, vacancies: List[Dict]):
        """Отправка уведомлений о новых вакансиях"""
        if not vacancies:
            return

        # Отправляем сообщение о начале поиска
        await self.bot.send_message(
            chat_id=chat_id,
            text=f"🔔 *Найдено {len(vacancies)} новых вакансий!*\n\n"
                 f"Вот самые свежие из них:",
            parse_mode='Markdown'
        )

        for i, vacancy in enumerate(vacancies[:3]):  # Ограничиваем 3 вакансиями за раз
            try:
                # Форматируем сообщение
                message = hh_client.format_vacancy_message(vacancy)

                # Добавляем заголовок
                notification_text = (
                    f"*Вакансия {i + 1} из {len(vacancies[:3])}*\n\n"
                    f"{message}"
                )

                # Отправляем сообщение
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=notification_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )

                # Задержка между сообщениями
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления: {e}")

        # Добавляем кнопку для просмотра всех вакансий
        if len(vacancies) > 3:
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Показать все вакансии", callback_data="show_all_vacancies")]
            ])

            await self.bot.send_message(
                chat_id=chat_id,
                text=f"📊 *Всего найдено {len(vacancies)} новых вакансий.*\n"
                     f"Нажмите кнопку ниже чтобы увидеть все результаты.",
                parse_mode='Markdown',
                reply_markup=keyboard
            )

    async def clear_user_history(self, user_id: int):
        """Очистка истории отправленных вакансий для пользователя"""
        if user_id in self.processed_vacancies:
            self.processed_vacancies[user_id].clear()
            logger.info(f"🧹 История вакансий очищена для пользователя {user_id}")

    async def get_scheduler_status(self) -> Dict:
        """Получение статуса планировщика"""
        jobs = self.scheduler.get_jobs()

        # Получаем статистику по пользователям
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.is_active == True)
            result = await session.execute(stmt)
            active_users = result.scalars().all()

            # Получаем пользователей с настройками фильтров
            users_with_filters = []
            for user in active_users:
                stmt = select(UserFilter).where(UserFilter.user_id == user.id)
                filter_result = await session.execute(stmt)
                if filter_result.scalars().first():
                    users_with_filters.append(user.id)

        return {
            'running': self.scheduler.running,
            'job_count': len(jobs),
            'next_run': jobs[0].next_run_time if jobs else None,
            'check_interval': self.check_interval,
            'users_tracked': len(self.processed_vacancies),
            'active_users': len(active_users),
            'users_with_filters': len(users_with_filters)
        }
