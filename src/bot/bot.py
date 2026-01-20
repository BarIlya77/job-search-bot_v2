from telegram.ext import Application
from src.bot.handlers.base import setup_handlers
from src.bot.handlers.filters import setup_callbacks as setup_filter_callbacks
from src.bot.handlers.vacancies import setup_callbacks as setup_vacancy_callbacks
from logger import get_logger

logger = get_logger(__name__)


async def setup_bot(token: str) -> Application:
    """Асинхронная настройка и конфигурация бота"""

    # Создаем приложение
    application = Application.builder().token(token).build()

    # Регистрируем обработчики
    logger.info("Регистрация обработчиков...")
    setup_handlers(application)

    # Callback-обработчики фильтров
    setup_filter_callbacks(application)

    # Callback-обработчики вакансий
    setup_vacancy_callbacks(application)

    logger.info("Бот сконфигурирован!")
    return application