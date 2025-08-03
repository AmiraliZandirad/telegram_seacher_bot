import asyncio
import re
import requests
from pyrogram import Client
from telegram.ext import Application, MessageHandler, filters

# تنظیمات
BOT_TOKEN = "8242002160:AAGDtD14wUI4EajkKnBDixqnUwDQXAhBtKE"
API_ID = 25517812
API_HASH = "1651908df3a7fb05ba65905ae0d32bc0"
SESSION_NAME = "car_user"
AI_API_URL = "https://api.avalai.ir/v1/"
AI_API_TOKEN = "aa-i65SVPZOrRHLjqR8RhXVRiAu61KD7rbgONplPMxem76igylU"

PRODUCTS = {}  # دیکشنری برای ذخیره محصولات و قیمت‌ها

# مقداردهی اولیه کلاینت Pyrogram
pyrogram_client = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

# تابع برای فراخوانی API خارجی (AvalAI)
def call_ai_api(message_text):
    try:
        headers = {"Authorization": f"Bearer {AI_API_TOKEN}"}
        payload = {"text": message_text}
        response = requests.post(AI_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()  # فرض می‌کنیم API پاسخ JSON برمی‌گرداند
    except Exception as e:
        print(f"خطا در فراخوانی API: {e}")
        return None

# تابع برای بررسی تمام پیام‌های تمام کانال‌ها
async def scrape_all_channels():
    async with pyrogram_client:
        # گرفتن تمام چت‌ها (کانال‌ها، گروه‌ها، و غیره)
        async for dialog in pyrogram_client.get_dialogs():
            chat = dialog.chat
            # فقط کانال‌ها و سوپردگروه‌ها را بررسی می‌کنیم
            if chat.type in ["channel", "supergroup"]:
                chat_username = chat.username if chat.username else chat.title
                print(f"در حال بررسی کانال: {chat_username}")
                try:
                    # گرفتن تعداد کل پیام‌ها
                    chat_info = await pyrogram_client.get_chat(chat.id)
                    total_messages = chat_info.messages_count if hasattr(chat_info, 'messages_count') else 1000
                    offset_id = 0
                    batch_size = 100  # تعداد پیام‌ها در هر درخواست

                    while True:
                        # گرفتن پیام‌ها به‌صورت دسته‌ای
                        messages = await pyrogram_client.get_chat_history(
                            chat.id, 
                            limit=batch_size, 
                            offset_id=offset_id
                        )
                        messages_list = [msg async for msg in messages]
                        if not messages_list:
                            break  # اگر پیام بیشتری نبود، حلقه را بشکن

                        for message in messages_list:
                            if message.text:
                                # فراخوانی API برای پردازش پیام (اختیاری)
                                ai_response = call_ai_api(message.text)
                                if ai_response and "product" in ai_response and "price" in ai_response:
                                    product_name = ai_response["product"].strip().lower()
                                    price = int(ai_response["price"])
                                else:
                                    # اگر API پاسخ نداد، از regex استفاده کن
                                    match = re.search(r"Product: (.*?),\s*Price: \$(\d+)", message.text, re.IGNORECASE)
                                    if match:
                                        product_name = match.group(1).strip().lower()
                                        price = int(match.group(2))
                                    else:
                                        continue  # پیام بدون فرمت مناسب

                                # ذخیره محصول و قیمت
                                if product_name in PRODUCTS:
                                    PRODUCTS[product_name].append((price, chat_username))
                                else:
                                    PRODUCTS[product_name] = [(price, chat_username)]

                        # به‌روزرسانی offset_id برای دسته بعدی
                        offset_id = messages_list[-1].id if messages_list else 0
                        await asyncio.sleep(0.5)  # تأخیر برای جلوگیری از محدودیت API

                        # اگر تعداد پیام‌های دریافت‌شده کمتر از batch_size بود، پایان پیام‌ها
                        if len(messages_list) < batch_size:
                            break

                    print(f"بررسی کانال {chat_username} تمام شد.")
                except Exception as e:
                    print(f"خطا در بررسی کانال {chat_username}: {e}")
        print("بررسی تمام کانال‌ها تمام شد. محصولات یافت‌شده:", PRODUCTS)

# تابع برای یافتن کمترین قیمت
def find_lowest_price(product_name):
    product_name = product_name.lower()
    if product_name in PRODUCTS:
        prices = PRODUCTS[product_name]
        lowest_price, channel = min(prices, key=lambda x: x[0])
        return f"کمترین قیمت برای {product_name}: ${lowest_price} در {channel}"
    return f"هیچ قیمتی برای {product_name} یافت نشد."

# هندلر پیام‌های کاربران
async def handle_message(update, context):
    user_query = update.message.text.strip().lower()
    response = find_lowest_price(user_query)
    await update.message.reply_text(response)

# تابع اصلی برای ربات تلگرام
async def main_telegram_bot():
    # مقداردهی اولیه ربات
    app = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلر برای پیام‌های متنی (به جز دستورات)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # شروع ربات
    print("شروع ربات تلگرام...")
    await app.run_polling()

# نقطه ورود اصلی
async def main():
    # ابتدا کانال‌ها را بررسی کن
    print("در حال بررسی تمام پیام‌های کانال‌ها...")
    await scrape_all_channels()
    
    # سپس ربات تلگرام را شروع کن
    await main_telegram_bot()

if __name__ == "__main__":
    asyncio.run(main())