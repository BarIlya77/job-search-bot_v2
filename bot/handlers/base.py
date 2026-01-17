from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from logger import get_logger
from bot.keyboards.main import get_main_keyboard

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    logger.info(f"Пользователь {update.effective_user.id} начал работу")

    await update.message.reply_text(
        "👋 Привет! Я бот для поиска работы на HH.ru.\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📋 Доступные команды:\n\n"
        "/start - Начать работу\n"
        "/help - Эта справка\n"
        "/filters - Настроить фильтры поиска\n"
        "/search - Найти вакансии\n"
        "/status - Показать статус\n\n"
        "Используйте кнопки для удобства!"
    )
    await update.message.reply_text(help_text)


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки главного меню"""
    text = update.message.text

    if text == "🔍 Поиск вакансий":
        await update.message.reply_text("Функция поиска в разработке...")
    elif text == "⚙️ Фильтры":
        await update.message.reply_text("Настройка фильтров в разработке...")
    elif text == "📊 Статус":
        await update.message.reply_text("Статус в разработке...")
    elif text == "❓ Помощь":
        await help_command(update, context)
    else:
        await update.message.reply_text(
            "Используйте кнопки меню или команды /help",
            reply_markup=get_main_keyboard()
        )


def setup_handlers(application):
    """Регистрация базовых обработчиков"""

    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Текстовые сообщения (кнопки главного меню)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
    )
    