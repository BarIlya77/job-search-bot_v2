from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from logger import get_logger
from src.bot.keyboards.main import get_main_keyboard
from src.bot.handlers.filters import filter_handler
from src.bot.handlers.vacancies import vacancy_handler
from src.services.scheduler_service import get_scheduler
from config import config

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} ({user.username}) начал работу")

    # СОЗДАЕМ ПОЛЬЗОВАТЕЛЯ В БАЗЕ
    from src.storage.database import AsyncSessionLocal
    from src.storage.models import User
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user.id)
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            existing_user.first_name = user.first_name
            existing_user.username = user.username
            existing_user.is_active = True
            logger.info(f"Обновлен пользователь {user.id}")
        else:
            new_user = User(
                telegram_id=user.id,
                first_name=user.first_name,
                username=user.username,
                is_active=True
            )
            session.add(new_user)
            logger.info(f"Создан новый пользователь {user.id}")

        await session.commit()

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
        "*/status* - Показать статус\n"
        "*/scheduler_status* - Статус планировщика\n"
        "*/scheduler_start* - Запустить планировщик\n"
        "*/scheduler_stop* - Остановить планировщик\n"
        "*/scheduler_interval 60* - Изменить интервал (в минутах)\n\n"
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


async def scheduler_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для проверки статуса планировщика"""
    scheduler = get_scheduler()

    if not scheduler:
        await update.message.reply_text(
            "❌ Планировщик не инициализирован",
            reply_markup=get_main_keyboard()
        )
        return

    try:
        status = await scheduler.get_scheduler_status()

        next_run = status['next_run']
        if next_run:
            # Форматируем дату без специальных символов
            next_run_str = next_run.strftime("%d.%m.%Y в %H:%M")
        else:
            next_run_str = "не запланировано"

        # Формируем сообщение БЕЗ Markdown
        status_text = (
            "📊 Статус планировщика\n\n"
            f"• Статус: {'🟢 Запущен' if status['running'] else '🔴 Остановлен'}\n"
            f"• Интервал проверки: {status['check_interval']} минут\n"
            f"• Следующая проверка: {next_run_str}\n"
            f"• Отслеживается пользователей: {status['users_tracked']}\n"
            f"• Активных пользователей: {status['active_users']}\n"
            f"• Пользователей с фильтрами: {status['users_with_filters']}\n"
            f"• Количество задач: {status['job_count']}\n\n"
            "Команды управления:\n"
            "/scheduler_start - запустить планировщик\n"
            "/scheduler_stop - остановить планировщик\n"
            "/scheduler_interval X - изменить интервал (в минутах)"
        )

        # Отправляем БЕЗ parse_mode
        await update.message.reply_text(
            status_text,
            reply_markup=get_main_keyboard(),
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Ошибка при получении статуса планировщика: {e}", exc_info=True)
        # Отправляем сообщение без Markdown на случай ошибки
        await update.message.reply_text(
            "📊 Статус планировщика:\n\n"
            f"Возникла ошибка при получении статуса.\n"
            f"Попробуйте позже или перезапустите планировщик.",
            reply_markup=get_main_keyboard()
        )


async def scheduler_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск планировщика"""
    scheduler = get_scheduler()

    if not scheduler:
        if update.message:
            await update.message.reply_text("❌ Планировщик не инициализирован")
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Планировщик не инициализирован"
            )
        return

    # Получаем интервал из аргументов или используем значение по умолчанию
    interval = config.CHECK_INTERVAL
    if context.args and len(context.args) > 0:
        try:
            interval = int(context.args[0])
            if interval < 5:
                if update.message:
                    await update.message.reply_text("❌ Интервал должен быть не менее 5 минут")
                elif update.effective_chat:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ Интервал должен быть не менее 5 минут"
                    )
                return
        except ValueError:
            error_message = "❌ Неверный формат числа. Используйте: /scheduler_start 60"
            if update.message:
                await update.message.reply_text(error_message)
            elif update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_message
                )
            return

    try:
        await scheduler.start(interval)
        success_message = f"✅ Планировщик запущен с интервалом {interval} минут!"

        if update.message:
            await update.message.reply_text(success_message)
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=success_message
            )
    except Exception as e:
        logger.error(f"Ошибка при запуске планировщика: {e}")
        error_message = f"❌ Ошибка при запуске планировщика: {str(e)[:100]}"
        if update.message:
            await update.message.reply_text(error_message)
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message
            )


async def scheduler_stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Остановка планировщика"""
    scheduler = get_scheduler()

    if not scheduler:
        if update.message:
            await update.message.reply_text("❌ Планировщик не инициализирован")
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Планировщик не инициализирован"
            )
        return

    try:
        await scheduler.stop()
        success_message = "🛑 Планировщик остановлен"

        if update.message:
            await update.message.reply_text(success_message)
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=success_message
            )
    except Exception as e:
        logger.error(f"Ошибка при остановке планировщика: {e}")
        error_message = f"❌ Ошибка при остановке планировщика: {str(e)[:100]}"
        if update.message:
            await update.message.reply_text(error_message)
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message
            )


async def scheduler_interval_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменение интервала планировщика"""
    scheduler = get_scheduler()

    if not scheduler:
        if update.message:
            await update.message.reply_text("❌ Планировщик не инициализирован")
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Планировщик не инициализирован"
            )
        return

    try:
        if not context.args:
            if update.message:
                await update.message.reply_text("❌ Укажите интервал в минутах: /scheduler_interval 60")
            elif update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Укажите интервал в минутах: /scheduler_interval 60"
                )
            return

        interval = int(context.args[0])
        if interval < 5:
            if update.message:
                await update.message.reply_text("❌ Интервал должен быть не менее 5 минут")
            elif update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Интервал должен быть не менее 5 минут"
                )
            return

        # Останавливаем текущий планировщик
        await scheduler.stop()

        # Запускаем с новым интервалом
        await scheduler.start(interval)

        success_message = f"✅ Интервал планировщика изменен на {interval} минут"

        if update.message:
            await update.message.reply_text(success_message)
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=success_message
            )

    except ValueError:
        error_message = "❌ Неверный формат числа. Используйте: /scheduler_interval 60"
        if update.message:
            await update.message.reply_text(error_message)
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message
            )
    except Exception as e:
        logger.error(f"Ошибка при изменении интервала планировщика: {e}")
        error_message = f"❌ Ошибка при изменении интервала: {str(e)[:100]}"
        if update.message:
            await update.message.reply_text(error_message)
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message
            )


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки главного меню"""
    text = update.message.text

    if text == "🔍 Поиск вакансий":
        await vacancy_handler.search_vacancies(update, context)

    elif text == "⚙️ Фильтры":
        await filter_handler.show_filters_menu(update, context, from_callback=False)

    elif text == "📊 Статус":
        await update.message.reply_text(
            "📊 Статус бота:\n\n"
            "✅ Бот запущен и работает\n"
            "⚙️ Фильтры: не настроены\n"
            "🔍 Поиск: не настроен\n"
            "⏰ Автопоиск: выключен\n\n"
            "Используйте /scheduler_status для подробной информации",
            reply_markup=get_main_keyboard()
        )
    elif text == "❓ Помощь":
        await help_command(update, context)
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
    application.add_handler(CommandHandler("scheduler_status", scheduler_status_command))
    application.add_handler(CommandHandler("scheduler_start", scheduler_start_command))
    application.add_handler(CommandHandler("scheduler_stop", scheduler_stop_command))
    application.add_handler(CommandHandler("scheduler_interval", scheduler_interval_command))

    # Текстовые сообщения (кнопки главного меню)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)
    )
