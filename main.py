import re
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait, PeerIdInvalid
from telegram.ext import Updater, MessageHandler, Filters

# اطلاعات اکانت مرجع
api_id = 25517812
api_hash = "1651908df3a7fb05ba65905ae0d32bc0"
session_name = "car_user"

# توکن ربات تلگرام
bot_token = "8242002160:AAGDtD14wUI4EajkKnBDixqnUwDQXAhBtKE"

# تابع جستجو در کانال‌ها
async def search_car_price(query: str):
    results = []
    price_pattern = re.compile(
        r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)(?:\s*(تومان|میلیون|هزار)?)',
        re.IGNORECASE
    )

    async with Client(session_name, api_id=api_id, api_hash=api_hash, no_updates=True) as app:
        async for dialog in app.get_dialogs():
            if dialog.chat.type == "channel":
                username = dialog.chat.username
                if not username:
                    continue
                try:
                    async for msg in app.search_messages(username, query, limit=20):
                        if msg.text:
                            matches = price_pattern.findall(msg.text)
                            for match in matches:
                                num_str, unit = match
                                # حذف کاما و نقطه از عدد
                                num = int(num_str.replace(',', '').replace('.', ''))
                                # تبدیل واحد به عدد تقریبی تومان
                                if unit:
                                    unit = unit.lower()
                                    if unit == 'میلیون':
                                        num *= 1_000_000
                                    elif unit == 'هزار':
                                        num *= 1_000
                                results.append((num, msg.text[:100], username, msg.message_id))
                except (PeerIdInvalid, FloodWait):
                    continue

    if results:
        results.sort(key=lambda x: x[0])
        price, text, channel, msg_id = results[0]
        return f"💰 کمترین قیمت: {price:,} تومان\n📄 متن: {text}\n🔗 https://t.me/{channel}/{msg_id}"
    else:
        return "❗ هیچ نتیجه‌ای پیدا نشد."

# هندلر پیام‌های ربات
def handle_message(update, context):
    query = update.message.text
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(search_car_price(query))
    update.message.reply_text(result)

# اجرای ربات
def main():
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
