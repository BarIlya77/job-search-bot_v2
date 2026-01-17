import asyncio
import logging
from bot.bot import setup_bot
from logger import get_logger
from config import config

logger = get_logger(__name__)


async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")

    # Инициализация базы данных (позже)
    # await init_database()

    # Настройка и запуск бота
    application = await setup_bot(config.BOT_TOKEN)

    logger.info("Бот запущен и готов к работе!")

    # Запуск polling
    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
