from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler
)
import logging
from typing import Dict, List
from enum import Enum, auto
from subjects_data import subjects_data  

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("university_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Conversatation stat
class State(Enum):
    LANGUAGE = auto()
    YEAR = auto()
    SEMESTER = auto()
    SUBJECT = auto()
    RESOURCE = auto()

#  messages
messages = {
    "en": {
        "welcome": "🏫 Welcome to the University of Science and Technology, Tissemsilt (CMT Branch) \n\nChoose your language:",
        "choose_year": "📅 Choose academic year:",
        "choose_semester": "📚 Choose semester:",
        "choose_subject": "📖 Choose subject:",
        "choose_resource": "📂 Choose content type:",
        "back": "🔙 Back",
        "help": "🆘 How to use the bot:\n\n"
                "1. Choose academic year\n"
                "2. Choose semester\n"
                "3. Choose subject\n"
                "4. Choose content type\n\n"
                "You can go back anytime using 🔙 button",
        "error": "⚠️ An error occurred! Please try again.",
        "no_content": "⛔ No content available for this option at the moment."
    },
    "ar": {
        "welcome": "🏫 مرحبًا بكم في بوت المواد الدراسية لجامعة العلوم والتكنولوجيا تيسمسيلت (فرع CMT)!\n\nاختر لغتك:",
        "choose_year": "📅 اختر السنة الدراسية:",
        "choose_semester": "📚 اختر السداسي الدراسي:",
        "choose_subject": "📖 اختر المادة:",
        "choose_resource": "📂 اختر نوع المحتوى:",
        "back": "🔙 رجوع",
        "help": "🆘 كيفية استخدام البوت:\n\n"
                "1. اختر السنة الدراسية\n"
                "2. اخترالسداسي الدراسي\n"
                "3. اختر المادة\n"
                "4. اختر نوع المحتوى\n\n"
                "يمكنك الرجوع في أي وقت باستخدام زر 🔙",
        "error": "⚠️ حدث خطأ! يرجى المحاولة مرة أخرى.",
        "no_content": "⛔ لا يوجد محتوى متاح لهذا الخيار حالياً."
    }
}

# User data storage
user_data = {}

def create_keyboard(buttons: List[List[Dict]], lang: str = "en", back_state: str = None) -> InlineKeyboardMarkup:
    """Create an inline keyboard with optional back button."""
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for button in row:
            if button.get("url"):
                keyboard_row.append(InlineKeyboardButton(button["text"], url=button["url"]))
            else:
                keyboard_row.append(InlineKeyboardButton(button["text"], callback_data=button["callback_data"]))
        keyboard.append(keyboard_row)
    
    # Add back button 
    if back_state:
        keyboard.append([InlineKeyboardButton(messages[lang]["back"], callback_data=f"back_{back_state}")])
    
    return InlineKeyboardMarkup(keyboard)

def language_keyboard() -> InlineKeyboardMarkup:
    """Create language selection keyboard."""
    buttons = [
        [
            {"text": "English 🇬🇧", "callback_data": "lang_en"},
            {"text": "العربية 🇩🇿", "callback_data": "lang_ar"}
        ]
    ]
    return create_keyboard(buttons)

def year_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Create year selection keyboard."""
    buttons = [
        [
            {"text": "First Year" if lang == "en" else "السنة الأولى", "callback_data": "year1"},
            {"text": "Second Year" if lang == "en" else "السنة الثانية", "callback_data": "year2"}
        ]
    ]
    return create_keyboard(buttons, lang, "LANGUAGE")

def semester_keyboard(year: str, lang: str) -> InlineKeyboardMarkup:
    """Create semester selection keyboard based on year."""
    if year == "year1":
        semesters = ["1", "2"]
    else:
        semesters = ["3", "4"]
    
    buttons = [[
        {
            "text": f"Semester {sem}" if lang == "en" else f"السداسي{sem}",
            "callback_data": f"sem{sem}"
        } for sem in semesters
    ]]
    return create_keyboard(buttons, lang, "YEAR")

def subjects_keyboard(year: str, sem: str, lang: str) -> InlineKeyboardMarkup:
    """Create subject selection keyboard."""
    semester_key = f"semester{sem}"
    if year not in subjects_data or semester_key not in subjects_data[year]:
        return None
    
    subjects = subjects_data[year][semester_key]
    buttons = [[{"text": subject, "callback_data": f"sub_{subject}"}] for subject in subjects.keys()]
    return create_keyboard(buttons, lang, f"SEMESTER_{year}")

def resources_keyboard(subject_data: Dict, lang: str, back_data: str) -> InlineKeyboardMarkup:
    """Create resources selection keyboard."""
    if not subject_data:
        return None
    
    buttons = [[{"text": resource, "url": link}] for resource, link in subject_data.items()]
    return create_keyboard(buttons, lang, back_data)

def start(update: Update, context: CallbackContext) -> int:
    """Start command handler."""
    user = update.message.from_user
    logger.info(f"User {user.id} started the bot")
    
    update.message.reply_text(
        messages["en"]["welcome"],
        reply_markup=language_keyboard()
    )
    return State.LANGUAGE.value

def help_command(update: Update, context: CallbackContext) -> None:
    """Help command handler."""
    user_id = update.message.from_user.id
    lang = user_data.get(user_id, {}).get("lang", "en")
    update.message.reply_text(messages[lang]["help"])

def handle_callback(update: Update, context: CallbackContext) -> int:
    """Main callback handler."""
    query = update.callback_query
    user = query.from_user
    callback_data = query.data
    query.answer()
    
    logger.info(f"User {user.id} pressed: {callback_data}")
    
    try:
        if callback_data.startswith("lang_"):
            return handle_language(query, callback_data)
        elif callback_data.startswith("year"):
            return handle_year(query, callback_data)
        elif callback_data.startswith("sem"):
            return handle_semester(query, callback_data)
        elif callback_data.startswith("sub_"):
            return handle_subject(query, callback_data)
        elif callback_data.startswith("back_"):
            return handle_back(query, callback_data)
    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        query.edit_message_text(messages["en"]["error"])
    return State.LANGUAGE.value

def handle_language(query, callback_data) -> int:
    """Handle language selection."""
    user_id = query.from_user.id
    lang = callback_data.replace("lang_", "")
    
    # Save user lang
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["lang"] = lang
    
    query.edit_message_text(
        messages[lang]["choose_year"],
        reply_markup=year_keyboard(lang)
    )
    return State.YEAR.value

def handle_year(query, callback_data) -> int:
    """Handle year selection."""
    year = callback_data
    user_id = query.from_user.id
    lang = user_data[user_id]["lang"]
    
    # Save selected year
    user_data[user_id]["year"] = year
    
    query.edit_message_text(
        messages[lang]["choose_semester"],
        reply_markup=semester_keyboard(year, lang)
    )
    return State.SEMESTER.value

def handle_semester(query, callback_data) -> int:
    """Handle semester selection."""
    sem = callback_data.replace("sem", "")
    user_id = query.from_user.id
    lang = user_data[user_id]["lang"]
    year = user_data[user_id]["year"]
    
    # Save selected smtr
    user_data[user_id]["sem"] = sem
    
    # Get subjects keyboard
    keyboard = subjects_keyboard(year, sem, lang)
    if not keyboard:
        query.edit_message_text(messages[lang]["no_content"])
        return State.SEMESTER.value
    
    query.edit_message_text(
        messages[lang]["choose_subject"],
        reply_markup=keyboard
    )
    return State.SUBJECT.value

def handle_subject(query, callback_data) -> int:
    """Handle subject selection."""
    subject = callback_data.replace("sub_", "")
    user_id = query.from_user.id
    lang = user_data[user_id]["lang"]
    year = user_data[user_id]["year"]
    sem = user_data[user_id]["sem"]
    
    # Save selected sbjt
    user_data[user_id]["subject"] = subject
    
    # Get subject resources
    semester_key = f"semester{sem}"
    subject_data = subjects_data[year][semester_key].get(subject, {})
    back_data = f"SUB_{year}_{sem}"
    
    # Get resources keyboard
    keyboard = resources_keyboard(subject_data, lang, back_data)
    if not keyboard:
        query.edit_message_text(messages[lang]["no_content"])
        return State.SUBJECT.value
    
    query.edit_message_text(
        f"📚 {subject}\n\n{messages[lang]['choose_resource']}",
        reply_markup=keyboard
    )
    return State.RESOURCE.value

def handle_back(query, callback_data) -> int:
    """Handle back button navigation."""
    parts = callback_data.split("_")
    back_type = parts[1].upper()
    user_id = query.from_user.id
    lang = user_data[user_id]["lang"]
    
    try:
        if back_type == "LANGUAGE":
            query.edit_message_text(
                messages[lang]["welcome"],
                reply_markup=language_keyboard()
            )
            return State.LANGUAGE.value
        
        elif back_type == "YEAR":
            query.edit_message_text(
                messages[lang]["choose_year"],
                reply_markup=year_keyboard(lang)
            )
            return State.YEAR.value
        
        elif back_type == "SEMESTER":
            year = user_data[user_id]["year"]
            query.edit_message_text(
                messages[lang]["choose_semester"],
                reply_markup=semester_keyboard(year, lang)
            )
            return State.SEMESTER.value
        
        elif back_type == "SUB":
            year = parts[2]
            sem = parts[3]
            query.edit_message_text(
                messages[lang]["choose_subject"],
                reply_markup=subjects_keyboard(year, sem, lang)
            )
            return State.SUBJECT.value
        
    except Exception as e:
        logger.error(f"Error handling back: {e}")
    
    query.edit_message_text(messages[lang]["error"])
    return State.LANGUAGE.value

def error_handler(update: Update, context: CallbackContext) -> None:
    """Error handler for the bot."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update.callback_query:
        user_id = update.callback_query.from_user.id
        lang = user_data.get(user_id, {}).get("lang", "en")
        update.callback_query.answer(messages[lang]["error"])
    elif update.message:
        user_id = update.message.from_user.id
        lang = user_data.get(user_id, {}).get("lang", "en")
        update.message.reply_text(messages[lang]["error"])

def main() -> None:
    """Start the bot."""
    # Token
    updater = Updater("7194132273:AAFFf4Q9J4YJFKPm0poQ1DEjKn4WJYSNgec", use_context=True)
    dp = updater.dispatcher

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            State.LANGUAGE.value: [CallbackQueryHandler(handle_callback)],
            State.YEAR.value: [CallbackQueryHandler(handle_callback)],
            State.SEMESTER.value: [CallbackQueryHandler(handle_callback)],
            State.SUBJECT.value: [CallbackQueryHandler(handle_callback)],
            State.RESOURCE.value: [CallbackQueryHandler(handle_callback)]
        },
        fallbacks=[CommandHandler('help', help_command)],
        allow_reentry=True
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('help', help_command))
    dp.add_error_handler(error_handler)

    updater.start_polling()
    logger.info("Bot is running and ready to serve!")
    updater.idle()

if __name__ == '__main__':
    main()
