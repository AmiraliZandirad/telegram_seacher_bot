import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument, InputMessagesFilterEmpty
from pytz import timezone

# تنظیم لاگ‌گیری
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# اطلاعات API و توکن ربات
BOT_TOKEN = "8242002160:AAGDtD14wUI4EajkKnBDixqnUwDQXAhBtKE"
API_ID = 25517812
API_HASH = "1651908df3a7fb05ba65905ae0d32bc0"

# تابع برای استخراج قیمت از متن
def extract_price(text):
    # پشتیبانی از اعداد فارسی و انگلیسی
    price_pattern = r'(\d{1,3}(?:[,\.]\d{3})*(?:\.\d+)?)\s*(?:تومان|میلیون|تومن)?'
    persian_digits = {'۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'}
    for persian, latin in persian_digits.items():
        text = text.replace(persian, latin)
    prices = re.findall(price_pattern, text, re.IGNORECASE)
    cleaned_prices = []
    for price in prices:
        try:
            cleaned_price = price.replace(',', '').replace('.', '')
            cleaned_prices.append(float(cleaned_price))
        except ValueError as e:
            logger.error(f"Error converting price {price}: {e}")
    return cleaned_prices

# تابع برای جستجو در کانال‌ها
async def search_in_channels(query, client):
    min_price = float('inf')
    min_price_message = None
    channel_count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            channel_count += 1
            logger.info(f"Searching in channel: {dialog.title}")
            try:
                async for message in client.iter_messages(dialog.id, search=query, limit=50):
                    if message.text:
                        logger.info(f"Found message in {dialog.title}: {message.text}")
                        prices = extract_price(message.text)
                        if prices and min(prices) < min_price:
                            min_price = min(prices)
                            min_price_message = message.text
            except Exception as e:
                logger.error(f"Error in channel {dialog.title}: {e}")
    logger.info(f"Total channels checked: {channel_count}")
    return min_price, min_price_message

# تابع شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً مدل خودرو را وارد کنید (مثلاً: پراید)")

# تابع مدیریت پیام‌های کاربر
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    logger.info(f"User query: {query}")
    await update.message.reply_text(f"در حال جستجوی {query}...")

    async with TelegramClient('session_name', API_ID, API_HASH) as client:
        try:
            min_price, min_price_message = await search_in_channels(query, client)
            if min_price == float('inf'):
                await update.message.reply_text(f"خودرویی با مدل {query} پیدا نشد.")
            else:
                await update.message.reply_text(f"کمترین قیمت پیدا شده: {min_price:,} تومان\n\nپیام: {min_price_message}")
        except Exception as e:
            logger.error(f"Error during search: {e}")
            await update.message.reply_text("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# تابع اصلی
def main():
    # تنظیم ربات بدون نیاز به job_queue_scheduler
    application = Application.builder().token(BOT_TOKEN).build()

    # هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # شروع ربات
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()