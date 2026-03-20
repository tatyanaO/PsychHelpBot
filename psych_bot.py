import os
import json
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# --- Настройки ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # ← БЕРИ ИЗ REPLIT SECRETS
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # ← БЕРИ ИЗ REPLIT SECRETS
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# --- Логирование ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Состояния для диалога ---
ASKING_1, ASKING_2, ASKING_3, OFFER = range(4)

# --- Файл для хранения данных пользователей ---
USER_DATA_FILE = "user_data.json"

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Начало диалога ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {"answers": []}
    save_user_data(user_data)
    await update.message.reply_text(
        "Привет! 👋 Я — ваш помощник в понимании внутренних программ, которые могут мешать вам жить свободно.\n\n"
        "Я задам вам 3 вопроса — ответьте честно. Это займёт 2–3 минуты.\n\n"
        "1. Что вас больше всего утомляет в отношениях с близкими?"
    )
    return ASKING_1

# --- Вопрос 1 ---
async def ask_question_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    user_data[user_id]["answers"].append(update.message.text)
    save_user_data(user_data)
    await update.message.reply_text(
        "2. Какое убеждение вы чаще всего слышите в своей голове (например: «я недостаточно хорош», «я должен всё контролировать»)?"
    )
    return ASKING_2

# --- Вопрос 2 ---
async def ask_question_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    user_data[user_id]["answers"].append(update.message.text)
    save_user_data(user_data)
    await update.message.reply_text(
        "3. Что бы вы хотели изменить в себе, но не знаете, как начать?"
    )
    return ASKING_3

# --- Вопрос 3 и анализ через DeepSeek ---
async def ask_question_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    user_data[user_id]["answers"].append(update.message.text)
    save_user_data(user_data)

    answers = user_data[user_id]["answers"]
    prompt = f"""Ты — эксперт по психологии и подсознанию. На основе ответов человека определи:
- Главную внутреннюю программу (например: "я должен быть идеальным", "мне нельзя просить о помощи")
- Её возможное происхождение (детство, травма, воспитание)
- Как она мешает сейчас в жизни
- Одно мягкое, поддерживающее утверждение, которое может помочь изменить эту программу

Ответь кратко, на русском, как дружеский совет от психолога. Не используй медицинские термины.

Ответы пользователя:
1. {answers[0]}
2. {answers[1]}
3. {answers[2]}"""

    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 300
        }
        response = requests.post(DEEPSEEK_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        analysis = response.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        analysis = "Извините, произошла ошибка при анализе. Пожалуйста, напишите мне в личные сообщения — я помогу лично."

    user_data[user_id]["analysis"] = analysis
    save_user_data(user_data)

    await update.message.reply_text(
        f"✨ Спасибо за честность. Вот что я увидел:\n\n{analysis}\n\n"
        f"Если это вам близко — я помогаю людям глубоко работать с такими программами через 30-дневную программу «Освобождение от внутренних преград».\n\n"
        f"Это включает:\n"
        f"- Ежедневные осознания\n"
        f"- 4 сессии со мной\n"
        f"- Персональную «Карту ваших программ»\n\n"
        f"Цена — 20 000 ₽. Сейчас есть 2 свободных места.\n\n"
        f"Хотите попробовать? Напишите «Да» — и я пришлю подробности.",
        reply_markup=None
    )
    return OFFER

# --- Предложение пакета ---
async def offer_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower()
    user_id = str(update.effective_user.id)
    if any(word in user_input for word in ["да", "хочу", "готов", "ок", "окей"]):
        await update.message.reply_text(
            "Отлично! 🌱\n\n"
            "Я отправлю вам подробности пакета «Освобождение от внутренних преград» в личные сообщения.\n\n"
            "Пожалуйста, напишите мне в Telegram: @your_telegram_handle (замените на свой)\n"
            "Или ответьте: «Отправь ссылку» — и я пришлю форму оплаты.\n\n"
            "Спасибо, что доверяете себе."
        )
    else:
        await update.message.reply_text(
            "Понимаю. Если вдруг захотите вернуться — просто напишите «Привет».\n\n"
            "Вы всегда можете найти себя снова. 💙"
        )
    return ConversationHandler.END

# --- Отмена ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён. Вы всегда можете начать заново — напишите /start.")
    return ConversationHandler.END

# --- Основной запуск ---
def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("❌ TELEGRAM_TOKEN не установлен! Добавьте его в Replit Secrets.")
    if not DEEPSEEK_API_KEY:
        raise ValueError("❌ DEEPSEEK_API_KEY не установлен! Добавьте его в Replit Secrets.")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question_1)],
            ASKING_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question_2)],
            ASKING_3: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question_3)],
            OFFER: [MessageHandler(filters.TEXT & ~filters.COMMAND, offer_package)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    print("✅ Бот запущен и готов к работе!")
    application.run_polling()

if __name__ == "__main__":
    main()
