from telegram import ReplyKeyboardMarkup

def get_main_keyboard():
    """Главное меню с кнопками"""
    keyboard = [
        ["🔍 Поиск вакансий", "⚙️ Фильтры"],
        ["📊 Статус", "❓ Помощь"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
