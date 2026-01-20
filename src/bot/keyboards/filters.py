from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Optional

def get_filters_main_keyboard(current_filters: Optional[Dict] = None) -> InlineKeyboardMarkup:
    """Главное меню настройки фильтров"""
    keyboard = [
        [InlineKeyboardButton("💼 Профессия", callback_data="filter_profession")],
        [InlineKeyboardButton("💰 Зарплата от", callback_data="filter_salary")],
        [InlineKeyboardButton("🎓 Опыт работы", callback_data="filter_experience")],
        [InlineKeyboardButton("📍 Формат работы", callback_data="filter_schedule")],
        [InlineKeyboardButton("🏢 Тип занятости", callback_data="filter_employment")],
        [InlineKeyboardButton("🌍 Город", callback_data="filter_area")],
        [
            InlineKeyboardButton("✅ Сохранить и выйти", callback_data="filters_save"),
            InlineKeyboardButton("🧹 Очистить все", callback_data="filters_clear")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_profession_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора профессии"""
    keyboard = [
        [InlineKeyboardButton("Python-разработчик", callback_data="prof_python")],
        [InlineKeyboardButton("Data Scientist", callback_data="prof_data_science")],
        [InlineKeyboardButton("Backend-разработчик", callback_data="prof_backend")],
        [InlineKeyboardButton("Frontend-разработчик", callback_data="prof_frontend")],
        [InlineKeyboardButton("DevOps", callback_data="prof_devops")],
        [InlineKeyboardButton("QA Engineer", callback_data="prof_qa")],
        [InlineKeyboardButton("Ввести свою", callback_data="prof_custom")],
        [InlineKeyboardButton("↩️ Назад", callback_data="back_to_filters")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_experience_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора опыта"""
    keyboard = [
        [InlineKeyboardButton("Без опыта", callback_data="exp_noExperience")],
        [InlineKeyboardButton("1-3 года", callback_data="exp_between1And3")],
        [InlineKeyboardButton("3-6 лет", callback_data="exp_between3And6")],
        [InlineKeyboardButton("Более 6 лет", callback_data="exp_moreThan6")],
        [InlineKeyboardButton("↩️ Назад", callback_data="back_to_filters")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_schedule_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора формата работы"""
    keyboard = [
        [InlineKeyboardButton("Офис", callback_data="schedule_office")],
        [InlineKeyboardButton("Удалённо", callback_data="schedule_remote")],
        [InlineKeyboardButton("Гибрид", callback_data="schedule_hybrid")],
        [InlineKeyboardButton("Гибкий график", callback_data="schedule_flexible")],
        [InlineKeyboardButton("↩️ Назад", callback_data="back_to_filters")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_employment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа занятости"""
    keyboard = [
        [InlineKeyboardButton("Полный день", callback_data="employment_fullDay")],
        [InlineKeyboardButton("Частичная", callback_data="employment_partDay")],
        [InlineKeyboardButton("Проектная", callback_data="employment_project")],
        [InlineKeyboardButton("Стажировка", callback_data="employment_internship")],
        [InlineKeyboardButton("↩️ Назад", callback_data="back_to_filters")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_area_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора города"""
    keyboard = [
        [InlineKeyboardButton("Москва", callback_data="area_1")],
        [InlineKeyboardButton("Санкт-Петербург", callback_data="area_2")],
        [InlineKeyboardButton("Новосибирск", callback_data="area_4")],
        [InlineKeyboardButton("Екатеринбург", callback_data="area_3")],
        [InlineKeyboardButton("Удалённо", callback_data="area_remote")],
        [InlineKeyboardButton("Ввести свой", callback_data="area_custom")],
        [InlineKeyboardButton("↩️ Назад", callback_data="back_to_filters")]
    ]
    return InlineKeyboardMarkup(keyboard)