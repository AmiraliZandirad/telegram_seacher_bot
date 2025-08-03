import re
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait, PeerIdInvalid
from telegram.ext import Updater, MessageHandler, Filters

# اطلاعات Pyrogram
api_id = 25517812
api_hash = "1651908df3a7fb05ba65905ae0d32bc0"
session_name = "car_user"

# توکن ربات
bot_token = "8242002160:AAGDtD14wUI4EajkKnBDixqnUwDQXAhBtKE"

# تابع جستجو
async def search_car_price(query: str):
    results = []
    # no_updates=True تا آپدیت‌های خودکار را نگیریم
    async with Client(session_name, api_id=api_id, api_hash=api_hash, no_updates=True) as app:
        async for dialog in app.get_dialogs():
            if dialog.chat.type == "channel":
                username = dialog.chat.username
                if not username:
                    continue
                try:
                    async for msg in app.search_messages(username, query, limit=10):
                        if msg.text:
                            m = re.search(r'\d[\d,.]*', msg.text.replace(',', ''))
                            if m:
                                price = int(m.group().replace('.', '').replace(',', ''))
                                results.append((price, msg.text[:100], username, msg.message_id))
                except (PeerIdInvalid, FloodWait):
                    continue

    if results:
        results.sort(key=lambda x: x[0])
        price, text, channel, msg_id = results[0]
        return f"💰 کمترین قیمت: {price} تومان\n📄 متن: {text}\n🔗 https://t.me/{channel}/{msg_id}"
    else:
        return "❗ هیچ نتیجه‌ای پیدا نشد."

# هندلر ربات
def handle_message(update, context):
    query = update.message.text
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(search_car_price(query))
    update.message.reply_text(result)

# اجرای ربات با python-telegram-bot v13
def main():
    # از نسخه 13 استفاده می‌کنیم
    updater = Updater(token=bot_token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
