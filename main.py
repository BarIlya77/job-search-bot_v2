# main.py
import asyncio
import nest_asyncio
from src.bot.bot import setup_bot
from logger import get_logger
from config import config
from src.storage.database import init_db

# Применяем nest_asyncio для разрешения конфликта event loops
nest_asyncio.apply()

logger = get_logger(__name__)


async def main():
    """Главная асинхронная функция запуска бота"""
    logger.info("Запуск бота...")

    # Инициализация базы данных
    await init_db()
    logger.info("База данных готова")

    # Настройка и запуск бота
    logger.info("Создание приложения...")
    application = await setup_bot(config.BOT_TOKEN)

    logger.info("Бот запущен и готов к работе!")

    # Запуск polling
    await application.run_polling()


if __name__ == "__main__":
    try:
        # Используем asyncio.run() с nest_asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
