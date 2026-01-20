from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from src.bot.keyboards.filters import (
    get_filters_main_keyboard, get_profession_keyboard, get_experience_keyboard,
    get_schedule_keyboard, get_employment_keyboard, get_area_keyboard
)
from src.bot.keyboards.main import get_main_keyboard
from src.storage.database import get_session
from src.storage.repositories.filter_repo import get_filter_repo
from logger import get_logger

logger = get_logger(__name__)


class FilterHandler:
    """Обработчик фильтров поиска"""

    def __init__(self):
        self.waiting_for_input = {}  # user_id -> filter_type

    def _format_filters_text(self, filters: dict) -> str:
        """Форматирует фильтры для отображения"""
        if not filters:
            return "❌ Фильтры не настроены"

        parts = []
        if filters.get('profession'):
            parts.append(f"💼 Профессия: {filters['profession']}")
        if filters.get('salary_min'):
            parts.append(f"💰 Зарплата от: {filters['salary_min']} руб.")
        if filters.get('experience'):
            exp_map = {
                'noExperience': 'Без опыта',
                'between1And3': '1-3 года',
                'between3And6': '3-6 лет',
                'moreThan6': 'Более 6 лет'
            }
            parts.append(f"🎓 Опыт: {exp_map.get(filters['experience'], filters['experience'])}")
        if filters.get('schedule'):
            schedule_map = {
                'office': 'Офис',
                'remote': 'Удалённо',
                'hybrid': 'Гибрид',
                'flexible': 'Гибкий график'
            }
            parts.append(f"📍 Формат: {schedule_map.get(filters['schedule'], filters['schedule'])}")
        if filters.get('employment'):
            employment_map = {
                'fullDay': 'Полный день',
                'partDay': 'Частичная',
                'project': 'Проектная',
                'internship': 'Стажировка'
            }
            parts.append(f"🏢 Занятость: {employment_map.get(filters['employment'], filters['employment'])}")
        if filters.get('area'):
            area_map = {
                '1': 'Москва',
                '2': 'Санкт-Петербург',
                '3': 'Екатеринбург',
                '4': 'Новосибирск',
                'remote': 'Удалённо'
            }
            area = filters['area']
            parts.append(f"🌍 Город: {area_map.get(area, area)}")

        return "\n".join(parts) if parts else "❌ Фильтры не настроены"

    async def show_filters_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                user_id: int = None, from_callback: bool = True):
        """Показать меню фильтров с текущими настройками"""
        if not user_id:
            if from_callback and update.callback_query:
                user_id = update.callback_query.from_user.id
            else:
                user_id = update.effective_user.id

        # Получаем текущие фильтры пользователя
        async for session in get_session():
            repo = get_filter_repo(session)
            current_filters = await repo.get_user_filters(user_id)

        # Формируем текст с текущими настройками
        filters_text = self._format_filters_text(current_filters)

        message_text = (
            f"⚙️ *Настройка фильтров поиска*\n\n"
            f"Текущие настройки:\n{filters_text}\n\n"
            f"Выберите параметр для настройки:"
        )

        if from_callback and update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=get_filters_main_keyboard(current_filters)
            )
        elif from_callback:
            await update.callback_query.edit_message_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=get_filters_main_keyboard(current_filters)
            )
        else:
            await update.message.reply_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=get_filters_main_keyboard(current_filters)
            )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех callback-запросов фильтров"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = query.from_user.id

        logger.info(f"Filter callback: {data} от {user_id}")

        # Обработка основных действий
        if data == "back_to_filters":
            await self.show_filters_menu(update, context, user_id, from_callback=True)

        elif data == "back_to_main":
            await query.edit_message_text(
                "Возврат в главное меню...",
                reply_markup=None
            )
            await context.bot.send_message(
                chat_id=user_id,
                text="Главное меню:",
                reply_markup=get_main_keyboard()
            )

        elif data.startswith("filter_"):
            await self.handle_filter_selection(update, context)

        elif data.startswith(("prof_", "exp_", "schedule_", "employment_", "area_")):
            await self.handle_filter_value(update, context)

        elif data.startswith("filters_"):
            await self.handle_filter_actions(update, context)

        else:
            await query.answer("❌ Неизвестная команда")

    async def handle_filter_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора типа фильтра"""
        query = update.callback_query
        data = query.data

        if data == "filter_profession":
            await query.edit_message_text(
                "💼 *Выберите профессию:*",
                parse_mode='Markdown',
                reply_markup=get_profession_keyboard()
            )

        elif data == "filter_salary":
            self.waiting_for_input[query.from_user.id] = 'salary_min'
            await query.edit_message_text(
                "💰 *Введите минимальную зарплату в рублях:*\n\n"
                "Пример: 100000",
                parse_mode='Markdown'
            )

        elif data == "filter_experience":
            await query.edit_message_text(
                "🎓 *Выберите требуемый опыт:*",
                parse_mode='Markdown',
                reply_markup=get_experience_keyboard()
            )

        elif data == "filter_schedule":
            await query.edit_message_text(
                "📍 *Выберите формат работы:*",
                parse_mode='Markdown',
                reply_markup=get_schedule_keyboard()
            )

        elif data == "filter_employment":
            await query.edit_message_text(
                "🏢 *Выберите тип занятости:*",
                parse_mode='Markdown',
                reply_markup=get_employment_keyboard()
            )

        elif data == "filter_area":
            await query.edit_message_text(
                "🌍 *Выберите город:*",
                parse_mode='Markdown',
                reply_markup=get_area_keyboard()
            )

    async def handle_filter_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора значения фильтра"""
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id

        try:
            if data.startswith("prof_"):
                profession = data.replace("prof_", "")
                if profession == "custom":
                    self.waiting_for_input[user_id] = 'profession'
                    await query.edit_message_text(
                        "💼 *Введите профессию:*\n\n"
                        "Пример: Python разработчик",
                        parse_mode='Markdown'
                    )
                else:
                    async for session in get_session():
                        repo = get_filter_repo(session)
                        await repo.save_filter(user_id, 'profession', profession)
                    await self.show_filters_menu(update, context, user_id, from_callback=True)

            elif data.startswith("exp_"):
                experience = data.replace("exp_", "")
                async for session in get_session():
                    repo = get_filter_repo(session)
                    await repo.save_filter(user_id, 'experience', experience)
                await self.show_filters_menu(update, context, user_id, from_callback=True)

            elif data.startswith("schedule_"):
                schedule = data.replace("schedule_", "")
                async for session in get_session():
                    repo = get_filter_repo(session)
                    await repo.save_filter(user_id, 'schedule', schedule)
                await self.show_filters_menu(update, context, user_id, from_callback=True)

            elif data.startswith("employment_"):
                employment = data.replace("employment_", "")
                async for session in get_session():
                    repo = get_filter_repo(session)
                    await repo.save_filter(user_id, 'employment', employment)
                await self.show_filters_menu(update, context, user_id, from_callback=True)

            elif data.startswith("area_"):
                area = data.replace("area_", "")
                if area == "custom":
                    self.waiting_for_input[user_id] = 'area'
                    await query.edit_message_text(
                        "🌍 *Введите город:*\n\n"
                        "Пример: Москва",
                        parse_mode='Markdown'
                    )
                else:
                    async for session in get_session():
                        repo = get_filter_repo(session)
                        await repo.save_filter(user_id, 'area', area)
                    await self.show_filters_menu(update, context, user_id, from_callback=True)
        except Exception as e:
            logger.error(f"Ошибка сохранения фильтра: {e}")
            await query.edit_message_text(
                f"❌ Ошибка при сохранении: {str(e)}",
                reply_markup=get_main_keyboard()
            )

    async def handle_filter_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка действий с фильтрами"""
        query = update.callback_query
        data = query.data
        user_id = query.from_user.id

        if data == "filters_save":
            # Просто возвращаем в главное меню
            await query.edit_message_text(
                "✅ Фильтры сохранены!",
                reply_markup=None
            )
            await context.bot.send_message(
                chat_id=user_id,
                text="Главное меню:",
                reply_markup=get_main_keyboard()
            )

        elif data == "filters_clear":
            async for session in get_session():
                repo = get_filter_repo(session)
                await repo.clear_all_filters(user_id)

            await query.edit_message_text(
                "🧹 Все фильтры очищены!",
                reply_markup=get_main_keyboard()
            )

    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстового ввода для фильтров"""
        user_id = update.effective_user.id

        if user_id not in self.waiting_for_input:
            return  # Не наш фильтр, пусть обрабатывается дальше

        filter_type = self.waiting_for_input.pop(user_id)
        text = update.message.text

        try:
            if filter_type == 'salary_min':
                # Проверяем, что введено число
                salary = ''.join(filter(str.isdigit, text))
                if not salary:
                    await update.message.reply_text("❌ Пожалуйста, введите число!")
                    self.waiting_for_input[user_id] = filter_type
                    return

                async for session in get_session():
                    repo = get_filter_repo(session)
                    await repo.save_filter(user_id, 'salary_min', salary)

                await update.message.reply_text(f"✅ Минимальная зарплата сохранена: {salary} руб.")

            elif filter_type == 'profession':
                async for session in get_session():
                    repo = get_filter_repo(session)
                    await repo.save_filter(user_id, 'profession', text)

                await update.message.reply_text(f"✅ Профессия сохранена: {text}")

            elif filter_type == 'area':
                async for session in get_session():
                    repo = get_filter_repo(session)
                    await repo.save_filter(user_id, 'area', text)

                await update.message.reply_text(f"✅ Город сохранен: {text}")

            # Показываем меню фильтров после сохранения
            await self.show_filters_menu(update, context, user_id, from_callback=False)

        except Exception as e:
            logger.error(f"Ошибка сохранения фильтра: {e}")
            await update.message.reply_text("❌ Ошибка при сохранении. Попробуйте снова.")


# Создаем экземпляр обработчика
filter_handler = FilterHandler()


# Функции для регистрации обработчиков
async def handle_filter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обертка для обработчика callback"""
    await filter_handler.handle_callback(update, context)


async def handle_filter_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обертка для обработчика текста"""
    await filter_handler.handle_text_input(update, context)


def setup_callbacks(application):
    """Регистрация обработчиков фильтров"""
    # Обработчик callback-запросов фильтров
    application.add_handler(
        CallbackQueryHandler(handle_filter_callback,
                             pattern="^(filter_|prof_|exp_|schedule_|employment_|area_|filters_|back_to_)")
    )

    # Обработчик текстового ввода для фильтров
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_filter_text),
        group=1  # Высокий приоритет
    )
