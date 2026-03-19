import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

# 🔐 Читаем токены из переменных окружения (НЕ в коде!)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🌱 Я — твой психологический помощник. "
        "Расскажи, что тебя тревожит — я здесь, чтобы выслушать и помочь."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я могу выслушать тебя и предложить поддержку. "
        "Просто напиши, что у тебя на душе. 💬\n\n"
        "Совет: не бойся быть честным — здесь ты в безопасности."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if not DEEPSEEK_API_KEY:
        await update.message.reply_text("Извини, я сейчас не могу обработать твой запрос. Попробуй позже.")
        return

    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Ты — доброжелательный, эмпатичный психолог. Отвечай кратко, тепло, поддерживая. Не давай медицинских советов. Сфокусируйся на эмоциональной поддержке."},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 300
            },
            timeout=10
        )
        reply = response.json().get("choices", [{}])[0].get("message", {}).get("content", "Я не понял, но я здесь для тебя. 🤗")
    except Exception:
        reply = "Извини, что-то пошло не так... Но я всё ещё здесь. 💙"

    await update.message.reply_text(reply)

def main():
    if not TELEGRAM_TOKEN:
        print("Ошибка: TELEGRAM_TOKEN не задан. Проверь переменные окружения.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stop", lambda u, c: u.message.reply_text("Если тебе станет хуже — не стесняйся обратиться за помощью к специалисту. Ты не один. 💙")))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()