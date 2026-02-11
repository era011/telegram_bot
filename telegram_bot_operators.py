import logging
import openai
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from db import init_db, save_message, get_last_messages
from weaviate_func import search


# Настройки
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY1"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я GPT-бот с памятью. Напиши мне что-нибудь.")

# Основной обработчик
async def chat_with_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Сохраняем сообщение пользователя
    save_message(user_id, "user", user_message)

    # Загружаем последние 10 пар сообщений
    messages = get_last_messages(user_id, limit=10)
    kb = search(user_message, limit=10)                      # Получаем базу знаний по запросу пользователя
    print(f'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  {messages}')
    print(f'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb    {kb}')
    # Добавляем system-промпт в начало
    messages.insert(0, {
        "role": "system",
        "content": f"""Ты помощник операторов АЗС компании RedPetroleum
        Ты должен отвечать на вопросы операторов, исходя из базы знаний
        Всегда указывай источник информации. Так же указывай url, если это возможно.
        Отвечать на вопросы либо на русском, либо на кыргызыском языке, в зависимости от языка вопроса.

        База знаний:

        {kb}"""
    })

    try:
        response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
        )
        reply_text = response.choices[0].message.content

        # Сохраняем ответ бота
        save_message(user_id, "assistant", reply_text)

        await update.message.reply_text(reply_text)

    except Exception as e:
        logging.error(f"Ошибка GPT: {e}")
        await update.message.reply_text("Произошла ошибка при запросе к GPT.")

# Сброс памяти
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    from db import DB_FILE
    import sqlite3
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    await update.message.reply_text("Память очищена!")

# Запуск
def main():
    init_db()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_gpt))

    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()