from telegram.ext import Application
from bot.handlers import base, filters, vacancies
from logger import get_logger

logger = get_logger(__name__)


async def setup_bot(token: str) -> Application:
    """Настройка и конфигурация бота"""

    # Создаем приложение
    application = Application.builder().token(token).build()

    # Регистрируем обработчики
    logger.info("Регистрация обработчиков...")

    # Команды
    base.setup_handlers(application)

    # Callback-обработчики (кнопки)
    filters.setup_callbacks(application)
    vacancies.setup_callbacks(application)

    return application
