import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument, InputMessagesFilterEmpty

# اطلاعات API و توکن ربات
BOT_TOKEN = "8242002160:AAGDtD14wUI4EajkKnBDixqnUwDQXAhBtKE"
API_ID = 25517812
API_HASH = "1651908df3a7fb05ba65905ae0d32bc0"

# تابع برای استخراج قیمت از متن
def extract_price(text):
    # جستجوی الگوهای قیمت (مانند 500,000,000 یا 500 میلیون)
    price_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:تومان|میلیون|تومن)?'
    prices = re.findall(price_pattern, text, re.IGNORECASE)
    return [float(price.replace(',', '')) for price in prices]

# تابع برای جستجو در کانال‌ها
async def search_in_channels(query, client):
    min_price = float('inf')
    min_price_message = None
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            try:
                async for message in client.iter_messages(dialog.id, search=query, limit=50):
                    if message.text:
                        prices = extract_price(message.text)
                        if prices and min(prices) < min_price:
                            min_price = min(prices)
                            min_price_message = message.text
            except Exception as e:
                print(f"Error in channel {dialog.title}: {e}")
    return min_price, min_price_message

# تابع شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً مدل خودرو را وارد کنید (مثلاً: پراید)")

# تابع مدیریت پیام‌های کاربر
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.reply_text(f"در حال جستجوی {query}...")

    # اتصال به تلگرام با Telethon
    async with TelegramClient('session_name', API_ID, API_HASH) as client:
        min_price, min_price_message = await search_in_channels(query, client)

        if min_price == float('inf'):
            await update.message.reply_text(f"خودرویی با مدل {query} پیدا نشد.")
        else:
            await update.message.reply_text(f"کمترین قیمت پیدا شده: {min_price:,} تومان\n\nپیام: {min_price_message}")

# تابع اصلی
def main():
    # تنظیم ربات
    application = Application.builder().token(BOT_TOKEN).build()

    # هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # شروع ربات
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()