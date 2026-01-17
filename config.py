import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jobs.db")

    # HH API
    HH_API_URL: str = "https://api.hh.ru/vacancies"
    HH_USER_AGENT: str = "JobBot/1.0"

    # DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")

    # Scheduler
    DEFAULT_CHECK_INTERVAL: int = 3600  # 1 час в секундах


config = Config()

# Валидация
if not config.BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен в .env файле")
