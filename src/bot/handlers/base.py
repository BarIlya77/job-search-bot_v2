from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from logger import get_logger
from src.bot.keyboards.main import get_main_keyboard
from src.bot.handlers.filters import filter_handler
from src.bot.handlers.vacancies import handle_search_command

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} ({user.username}) начал работу")

    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я — бот для поиска работы на HH.ru.\n"
        "Используй кнопки ниже для управления:\n\n"
        "• 🔍 **Поиск вакансий** — найти новые вакансии\n"
        "• ⚙️ **Фильтры** — настроить параметры поиска\n"
        "• 📊 **Статус** — текущие настройки\n"
        "• ❓ **Помощь** — список всех команд"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📋 *Доступные команды:*\n\n"
        "*/start* - Начать работу с ботом\n"
        "*/help* - Показать это сообщение\n"
        "*/status* - Показать статус\n\n"
        "⚙️ *Меню:*\n"
        "• 🔍 Поиск вакансий\n"
        "• ⚙️ Фильтры\n"
        "• 📊 Статус\n"
        "• ❓ Помощь"
    )

    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда для проверки работы"""
    await update.message.reply_text("✅ Бот работает корректно!")


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки главного меню"""
    text = update.message.text

    if text == "🔍 Поиск вакансий":
        from src.bot.handlers.vacancies import vacancy_handler
        await vacancy_handler.search_vacancies(update, context)
    elif text == "⚙️ Фильтры":
        # Используем фильтр хендлер для показа меню фильтров
        await filter_handler.show_filters_menu(update, context, from_callback=False)

    elif text == "📊 Статус":
        await update.message.reply_text(
            "📊 Статус бота:\n\n"
            "✅ Бот запущен и работает\n"
            "⚙️ Фильтры: не настроены\n"
            "🔍 Поиск: не настроен\n"
            "⏰ Автопоиск: выключен",
            reply_markup=get_main_keyboard()
        )
    elif text == "❓ Помощь":
        await help_command(update, context)
    elif text == "Test":
        await test_command(update, context)
    else:
        await update.message.reply_text(
            "🤖 Я понимаю только команды из меню.\n\n"
            "Используйте кнопки ниже для навигации:",
            reply_markup=get_main_keyboard()
        )


def setup_handlers(application):
    """Регистрация базовых обработчиков"""

    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("search", handle_search_command))

    # Текстовые сообщения (кнопки главного меню)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
    )
