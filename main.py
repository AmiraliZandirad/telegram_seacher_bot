from pyrogram import Client
from pyrogram.errors import FloodWait, PeerIdInvalid
from pyrogram.types import Message
from telegram.ext import Updater, MessageHandler, Filters
import asyncio
import re


api_id = 25517812
api_hash = "1651908df3a7fb05ba65905ae0d32bc0"
session_name = "car_user"


bot_token = "8242002160:AAGDtD14wUI4EajkKnBDixqnUwDQXAhBtKE"



async def search_car_price(query):
    results = []
    async with Client(session_name, api_id=api_id, api_hash=api_hash, proxy=proxy) as app:
        async for dialog in app.get_dialogs():
            if dialog.chat.type in ["channel"]:
                username = dialog.chat.username
                if not username:
                    continue
                try:
                    async for msg in app.search_messages(username, query, limit=10):
                        if msg.text:
                            price_match = re.search(r'\d[\d,.]*', msg.text.replace(',', ''))
                            if price_match:
                                price = int(price_match.group().replace('.', '').replace(',', ''))
                                results.append(price)
                except (PeerIdInvalid, FloodWait):
                    continue

    if results:
        min_price = min(results)
        return f"💰 کمترین قیمت: {min_price:,} تومان"
    else:
        return "❗ هیچ نتیجه‌ای پیدا نشد."


def handle_message(update, context):
    query = update.message.text
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(search_car_price(query))
    update.message.reply_text(result)


def main():
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()