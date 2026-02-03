import logging
import sys
from typing import Optional
from config import config

class CustomFormatter(logging.Formatter):
    """Кастомный форматтер для цветного вывода"""

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;20m"
    blue = "\x1b[34;20m"
    reset = "\x1b[0m"

    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: blue + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Создает и настраивает логгер"""
    logger = logging.getLogger(name or "job_bot")

    if not logger.handlers:
        # Устанавливаем уровень логирования из конфига
        log_level = getattr(logging, config.LOG_LEVEL.upper())
        logger.setLevel(log_level)

        # Создаем обработчик для stdout
        handler = logging.StreamHandler(sys.stdout)

        # Используем цветной форматтер
        handler.setFormatter(CustomFormatter())

        logger.addHandler(handler)

    return logger
