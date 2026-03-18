import logging
import openai
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from db import init_db, save_message, get_last_messages
from langgraph1.agent import graph  # <-- ПРОВЕРЬ ПУТЬ: где лежит graph = builder.compile()
from telegram.constants import ChatAction
import asyncio
from telegram.constants import ParseMode
import re


client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я помощник операторов АЗС Redpetroleum. Задай вопрос 🙂")


def _to_langgraph_messages(history: list[dict]) -> list[dict]:
    """
    Приводим историю к формату сообщений, который понимают LLM/Graph:
    [{"role":"user"/"assistant"/"system", "content":"..."}]
    """
    out = []
    for m in history:
        role = m.get("role")
        content = m.get("content")
        if role not in ("user", "assistant", "system"):
            continue
        if not content:
            continue
        out.append({"role": role, "content": content})
    return out

async def typing_indicator(bot, chat_id, stop_event: asyncio.Event):
    try:
        while not stop_event.is_set():
            await bot.send_chat_action(
                chat_id=chat_id,
                action=ChatAction.TYPING
            )
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass



def clean_html_for_telegram(text: str) -> str:
    if not text:
        return text

    # заменяем списки на нормальные bullets
    text = re.sub(r"<li>\s*", "• ", text)
    text = re.sub(r"</li>", "\n", text)

    # убираем ul/ol теги
    text = re.sub(r"</?ul>", "", text)
    text = re.sub(r"</?ol>", "", text)

    # убираем лишние переносы
    text = re.sub(r"\n+", "\n", text)

    return text.strip()



async def safe_send(update, text):
    text = clean_html_for_telegram(text)

    try:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"HTML parse error: {e}")
        await update.message.reply_text(text)
        
        

import asyncio
from telegram.constants import ChatAction

async def chat_with_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_message = (update.message.text or "").strip()
    if not user_message:
        await update.message.reply_text("Напиши вопрос текстом 🙂")
        return
    save_message(user_id, "user", user_message)
    history = get_last_messages(user_id, limit=15)
    history_msgs = _to_langgraph_messages(history)
    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(
        typing_indicator(context.bot, chat_id, stop_event)
    )
    try:
        state_in = {"messages": history_msgs + [{"role": "user", "content": user_message}]}
        state_out = await graph.ainvoke(state_in)
        msgs_out = state_out.get("messages", [])
        if not msgs_out:
            reply_text = "Не смог сформировать ответ."
        else:
            last = msgs_out[-1]
            reply_text = getattr(last, "content", "") if not isinstance(last, dict) else last.get("content", "")
        save_message(user_id, "assistant", reply_text)
        await safe_send(update, reply_text)
    except Exception:
        logging.exception("Graph error")
        await update.message.reply_text("Произошла ошибка при обработке запроса.")
    finally:
        # 🔹 останавливаем typing
        stop_event.set()
        typing_task.cancel()




async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.exception("Exception while handling an update:", exc_info=context.error)


def main():
    try:
        init_db()

        app = Application.builder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        # app.add_handler(CommandHandler("reset", reset))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_gpt))
        app.add_error_handler(error_handler)

        print("Бот запущен!")
        app.run_polling()
    except:
        client.close()    
    finally:
        client.close()    


if __name__ == "__main__":
    main()
