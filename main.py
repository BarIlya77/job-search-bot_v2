import asyncio
import nest_asyncio
from src.bot.bot import setup_bot
from logger import get_logger
from config import config
from src.storage.database import init_db
from src.services.scheduler_service import init_scheduler

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

    # Инициализация планировщика
    scheduler = None
    if config.SCHEDULER_ENABLED:
        scheduler = init_scheduler(application.bot)
        await scheduler.start(config.CHECK_INTERVAL)
        logger.info(f"✅ Планировщик запущен с интервалом {config.CHECK_INTERVAL} минут")

    logger.info("Бот запущен и готов к работе!")

    try:
        # Запуск polling
        await application.run_polling()
    finally:
        # Остановка планировщика при завершении работы
        if scheduler:
            await scheduler.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
