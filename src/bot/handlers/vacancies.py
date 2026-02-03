from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from logger import get_logger
from src.services.hh_client import hh_client
from src.services.filter_service import filter_service
from src.bot.keyboards.main import get_main_keyboard

logger = get_logger(__name__)


class VacancyHandler:
    """Обработчик вакансий"""

    def __init__(self):
        self.user_searches = {}  # user_id -> {'vacancies': [], 'current_index': 0}

    async def search_vacancies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Поиск вакансий по фильтрам пользователя"""
        user_id = update.effective_user.id

        # Отправляем сообщение о начале поиска
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                "🔍 Ищу вакансии по вашим фильтрам...",
                reply_markup=get_main_keyboard()
            )

        # Получаем фильтры пользователя
        filters = await filter_service.get_user_filters(user_id)

        if not filters:
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    "❌ У вас не настроены фильтры поиска.\n\n"
                    "Сначала настройте фильтры в меню ⚙️ Фильтры",
                    reply_markup=get_main_keyboard()
                )
            return

        # Преобразуем фильтры в параметры HH API
        params = await filter_service.to_hh_params(filters)

        # Если нет текстового запроса, используем что-то по умолчанию
        if not params.get('text'):
            params['text'] = 'разработчик'

        logger.info(f"Поиск с параметрами: {params}")

        try:
            # Ищем вакансии
            vacancies = await hh_client.search_vacancies(**params)

            if not vacancies:
                if hasattr(update, 'message') and update.message:
                    await update.message.reply_text(
                        "😔 По вашим фильтрам ничего не найдено.\n\n"
                        "Попробуйте изменить параметры поиска.",
                        reply_markup=get_main_keyboard()
                    )
                return

            # Сохраняем результаты поиска
            self.user_searches[user_id] = {
                'vacancies': vacancies,
                'current_index': 0
            }

            # Отправляем первую вакансию
            await self.send_vacancy(update, context, user_id, 0)

        except Exception as e:
            logger.error(f"Ошибка при поиске вакансий: {e}", exc_info=True)
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(
                    f"❌ Ошибка при поиске: {str(e)[:100]}",
                    reply_markup=get_main_keyboard()
                )

    async def send_vacancy(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                           user_id: int, index: int):
        """Отправка вакансии с навигацией"""
        if user_id not in self.user_searches:
            await self._send_error_message(update)
            return

        search_data = self.user_searches[user_id]
        vacancies = search_data['vacancies']

        if index >= len(vacancies):
            await self._send_end_of_search_message(update)
            return

        # Получаем вакансию
        vacancy = vacancies[index]

        # Форматируем сообщение
        message = hh_client.format_vacancy_message(vacancy)

        # Создаем клавиатуру навигации
        keyboard = self._create_navigation_keyboard(user_id, index, len(vacancies), vacancy.get('id'))

        # Отправляем или редактируем сообщение
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
        elif hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=keyboard,
                disable_web_page_preview=True
            )

        # Обновляем текущий индекс
        search_data['current_index'] = index

    def _create_navigation_keyboard(self, user_id: int, current_index: int,
                                    total: int, vacancy_id: str) -> InlineKeyboardMarkup:
        """Создание клавиатуры навигации по вакансиям"""
        keyboard = []

        # Кнопки навигации
        nav_buttons = []

        if current_index > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"prev_{current_index - 1}"))

        nav_buttons.append(InlineKeyboardButton(f"{current_index + 1}/{total}", callback_data="page_info"))

        if current_index < total - 1:
            nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"next_{current_index + 1}"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        # Действия с вакансией
        action_buttons = [
            InlineKeyboardButton("💾 Сохранить", callback_data=f"save_{vacancy_id}"),
            InlineKeyboardButton("👎 Скрыть", callback_data=f"hide_{vacancy_id}"),
            InlineKeyboardButton("📝 Письмо", callback_data=f"cover_{vacancy_id}")
        ]
        keyboard.append(action_buttons)

        # Возврат
        keyboard.append([InlineKeyboardButton("🔙 В меню", callback_data="back_to_main")])

        return InlineKeyboardMarkup(keyboard)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback для вакансий"""
        query = update.callback_query
        await query.answer()

        data = query.data
        user_id = query.from_user.id

        logger.info(f"Vacancy callback: {data} от {user_id}")

        if data == "back_to_main":
            await query.edit_message_text(
                "Возврат в главное меню...",
                reply_markup=None
            )
            await context.bot.send_message(
                chat_id=user_id,
                text="Главное меню:",
                reply_markup=get_main_keyboard()
            )

        elif data.startswith("next_"):
            next_index = int(data.replace("next_", ""))
            await self.send_vacancy(update, context, user_id, next_index)

        elif data.startswith("prev_"):
            prev_index = int(data.replace("prev_", ""))
            await self.send_vacancy(update, context, user_id, prev_index)

        elif data.startswith("save_"):
            vacancy_id = data.replace("save_", "")
            await query.answer("💾 Вакансия сохранена в избранное!")

        elif data.startswith("hide_"):
            vacancy_id = data.replace("hide_", "")
            await query.answer("👎 Больше не показывать эту вакансию")

        elif data.startswith("cover_"):
            vacancy_id = data.replace("cover_", "")
            await query.answer("📝 Функция в разработке")

        elif data == "show_all_vacancies":
            # Инициируем обычный поиск вакансий
            await query.answer("🔍 Запускаю поиск всех вакансий...")
            await self.search_vacancies(update, context)

        elif data == "page_info":
            await query.answer(f"Текущая страница")

    async def _send_error_message(self, update: Update):
        """Сообщение об ошибке"""
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                "❌ Ошибка при поиске вакансий.\n\n"
                "Попробуйте позже или измените фильтры.",
                reply_markup=get_main_keyboard()
            )

    async def _send_end_of_search_message(self, update: Update):
        """Сообщение о конце списка вакансий"""
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(
                "✅ Это все найденные вакансии!\n\n"
                "Измените фильтры для нового поиска.",
                reply_markup=get_main_keyboard()
            )


# Создаем экземпляр обработчика
vacancy_handler = VacancyHandler()


# Функции для регистрации обработчиков
async def handle_vacancy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обертка для обработчика callback вакансий"""
    await vacancy_handler.handle_callback(update, context)


async def handle_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды поиска"""
    await vacancy_handler.search_vacancies(update, context)


def setup_callbacks(application):
    """Регистрация обработчиков вакансий"""
    # Обработчик callback-запросов вакансий
    application.add_handler(
        CallbackQueryHandler(
            handle_vacancy_callback,
            pattern="^(next_|prev_|save_|hide_|cover_|back_to_main|page_info)"
        )
    )
