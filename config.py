import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/jobs.db")
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite").lower()

    # HH API
    HH_API_URL: str = "https://api.hh.ru/vacancies"
    HH_USER_AGENT: str = "JobBot/1.0"

    # DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

    # Scheduler
    CHECK_INTERVAL: int = int(os.getenv("CHECK_INTERVAL", "3600"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self):
        """Валидация конфигурации"""
        if not self.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN не установлен в .env файле")

        # Для SQLite создаем директорию данных
        if self.DB_TYPE == "sqlite" and "sqlite" in self.DATABASE_URL:
            os.makedirs("./data", exist_ok=True)


config = Config()