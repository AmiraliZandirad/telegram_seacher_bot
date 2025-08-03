import asyncio
import re
import sqlite3
from pyrogram import Client
from telegram.ext import Application, MessageHandler, filters, CommandHandler
import logging
from pyrogram.errors import FloodWait

# تنظیمات لاگ‌گیری
logging.basicConfig(
    filename='bot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# تنظیمات
BOT_TOKEN = "8242002160:AAGDtD14wUI4EajkKnBDixqnUwDQXAhBtKE"
API_ID = 25517812
API_HASH = "1651908df3a7fb05ba65905ae0d32bc0"
SESSION_NAME = "car_user"

# لیست کانال‌های مشخص‌شده
TARGET_CHANNELS = [
    "@ArefzadehSales",
    "@bolvar_danesh_amoz",
    "@autobarbodgrop",
    "@car_ayral",
    "@autojaloulimohammad",
    "@khanehyma",
    "@otogaleryqasemi"
]

PRODUCTS = {}  # دیکشنری برای ذخیره محصولات و قیمت‌ها

# اتصال به پایگاه داده SQLite
conn = sqlite3.connect('products.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS products
             (name TEXT, price INTEGER, channel TEXT, contact TEXT, seller TEXT, model_year TEXT, details TEXT)''')
conn.commit()

# مقداردهی اولیه کلاینت Pyrogram
pyrogram_client = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH, workdir=".")

# تابع برای بررسی 50 پیام آخر کانال‌های مشخص‌شده
async def scrape_target_channels():
    async with pyrogram_client:
        try:
            logger.info("شروع بررسی کانال‌های مشخص‌شده")
            print("شروع بررسی کانال‌های مشخص‌شده")
            for channel in TARGET_CHANNELS:
                try:
                    # دریافت اطلاعات کانال
                    chat = await pyrogram_client.get_chat(channel)
                    chat_username = chat.username if chat.username else chat.title
                    logger.info(f"در حال بررسی کانال: {chat_username} (ID: {chat.id})")
                    print(f"در حال بررسی کانال: {chat_username} (ID: {chat.id})")

                    # دریافت فقط 50 پیام آخر
                    messages = await pyrogram_client.get_chat_history(chat.id, limit=50)
                    messages_list = [msg async for msg in messages]
                    logger.info(f"تعداد پیام‌های دریافت‌شده از {chat_username}: {len(messages_list)}")
                    print(f"تعداد پیام‌های دریافت‌شده از {chat_username}: {len(messages_list)}")

                    for message in messages_list:
                        if message.text:
                            logger.debug(f"پیام در {chat_username}: {message.text[:200]}...")
                            # الگوهای regex برای فرمت‌های مختلف
                            patterns = [
                                # فرمت پیام‌های نمونه (مثل دفتر فروش عارف زاده)
                                r"(.*?)\n.*?مدل\s*(\d{4}|۱\d{3}).*?\n(?:قیمت|فی)[:\s]*(\d+[.,/]?[\d]*)[\s]*(?:تومان)?\n.*?(?:\n(\d{10,11}))?(?:.*?\n(\d{10,11}))?(?:\n(.*))?",
                                # فرمت عمومی‌تر
                                r"(.*?)\s*(?:مدل|سال)\s*(\d{4}|۱\d{3})?\s*(?:قیمت|فی)[:\s]*(\d+[.,/]?[\d]*)[\s]*(?:تومان)?\s*(?:تماس|شماره)?\s*(\d{10,11})?\s*(.*)?",
                                # فرمت ساده بدون مدل
                                r"(.*?)\s*(?:قیمت|فی)[:\s]*(\d+[.,/]?[\d]*)[\s]*(?:تومان)?\s*(?:تماس|شماره)?\s*(\d{10,11})?\s*(.*)?",
                            ]
                            product_name = None
                            price = None
                            contact = None
                            seller = None
                            model_year = None
                            details = None
                            for pattern in patterns:
                                match = re.search(pattern, message.text, re.IGNORECASE | re.MULTILINE)
                                if match:
                                    product_name = match.group(1).strip().lower()
                                    price_str = match.group(2 if pattern == patterns[2] else 3).replace(",", "").replace(".", "").replace("/", "")
                                    price = int(price_str) * (1000000 if len(price_str) <= 4 else 1)
                                    model_year = match.group(2) if match.group(2) else "نامشخص"
                                    contact = ", ".join(filter(None, [match.group(3 if pattern == patterns[2] else 4), match.group(5)])) if match.group(3 if pattern == patterns[2] else 4) or match.group(5) else ""
                                    seller = match.group(4 if pattern == patterns[2] else 6).strip() if match.group(4 if pattern == patterns[2] else 6) else "نامشخص"
                                    details = message.text
                                    logger.info(f"استخراج: {product_name}, {price:,} تومان, مدل: {model_year}, تماس: {contact}, فروشنده: {seller}")
                                    print(f"استخراج: {product_name}, {price:,} تومان, مدل: {model_year}, تماس: {contact}, فروشنده: {seller}")
                                    break

                            if product_name and price:
                                contacts = re.findall(r"\d{10,11}", message.text)
                                contact = ", ".join(contacts) if contacts else ""
                                PRODUCTS[product_name] = PRODUCTS.get(product_name, []) + [(price, chat_username, contact, seller, model_year, details)]
                                c.execute("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)",
                                          (product_name, price, chat_username, contact, seller, model_year, details))
                                conn.commit()

                    await asyncio.sleep(1)  # تأخیر برای جلوگیری از FloodWait

                except FloodWait as e:
                    logger.warning(f"محدودیت API در کانال {channel}: منتظر {e.value} ثانیه")
                    print(f"محدودیت API در کانال {channel}: منتظر {e.value} ثانیه")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    logger.error(f"خطا در بررسی کانال {channel}: {e}")
                    print(f"خطا در بررسی کانال {channel}: {e}")
                    continue
        except Exception as e:
            logger.error(f"خطا در گرفتن چت‌ها: {e}")
            print(f"خطا در گرفتن چت‌ها: {e}")
        logger.info(f"بررسی تمام کانال‌ها تمام شد. محصولات یافت‌شده: {len(PRODUCTS)}")
        print(f"بررسی تمام کانال‌ها تمام شد. محصولات یافت‌شده: {len(PRODUCTS)}")

# تابع برای یافتن کمترین قیمت
def find_lowest_price(product_name):
    product_name = product_name.lower().strip()
    matching_products = []

    # جستجو در کلیدهای PRODUCTS
    for prod in PRODUCTS:
        if product_name in prod.lower():
            matching_products.append(prod)

    # جستجو در پایگاه داده با LIKE
    c.execute("SELECT * FROM products WHERE name LIKE ? OR details LIKE ?", (f"%{product_name}%", f"%{product_name}%"))
    rows = c.fetchall()
    for row in rows:
        prod = row[0].lower()
        if prod not in matching_products:
            matching_products.append(prod)
            PRODUCTS[prod] = PRODUCTS.get(prod, []) + [(row[1], row[2], row[3], row[4], row[5], row[6])]

    if matching_products:
        all_prices = []
        for prod in matching_products:
            all_prices.extend(PRODUCTS[prod])
        if all_prices:
            # یافتن کمترین قیمت
            lowest_price_item = min(all_prices, key=lambda x: x[0])
            price, channel, contact, seller, model_year, details = lowest_price_item
            response = f"کمترین قیمت برای {product_name}:\n{prod}: {price:,} تومان\nکانال: {channel}\nمدل: {model_year}"
            if contact:
                response += f"\nتماس: {contact}"
            if seller:
                response += f"\nفروشنده: {seller}"
            if details:
                response += f"\nجزئیات: {details[:200]}..." if len(details) > 200 else f"\nجزئیات: {details}"
            logger.info(f"جستجو برای {product_name}: کمترین قیمت {price:,} تومان")
            return response
    logger.warning(f"هیچ آگهی برای {product_name} یافت نشد.")
    return f"هیچ آگهی برای {product_name} یافت نشد."

# هندلر پیام‌های کاربران
async def handle_message(update, context):
    user_query = update.message.text.strip()
    await update.message.reply_text("لطفا منتظر بمانید...")
    response = find_lowest_price(user_query)
    await update.message.reply_text(response)

# هندلر دستور /start
async def start(update, context):
    await update.message.reply_text("به ربات جستجوی قیمت خودرو خوش آمدید! نام خودرو (مثل 'تیگو ۸' یا 'دنا') را وارد کنید تا کمترین قیمت را پیدا کنم.")

# تابع اصلی برای ربات تلگرام
async def main_telegram_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("شروع ربات تلگرام...")
    print("شروع ربات تلگرام...")
    await app.run_polling()

# تابع اصلی
async def main():
    try:
        # اجرای ربات تلگرام و اسکرپ کردن به صورت همزمان
        telegram_task = asyncio.create_task(main_telegram_bot())
        while True:
            PRODUCTS.clear()
            c.execute("DELETE FROM products")
            conn.commit()
            await scrape_target_channels()
            await asyncio.sleep(600)  # به‌روزرسانی هر 10 دقیقه
            logger.info("به‌روزرسانی دوره‌ای انجام شد.")
            print("به‌روزرسانی دوره‌ای انجام شد.")
    except KeyboardInterrupt:
        logger.info("برنامه توسط کاربر متوقف شد.")
        print("برنامه توسط کاربر متوقف شد.")
    except Exception as e:
        logger.error(f"خطا در اجرای اصلی: {e}")
        print(f"خطا در اجرای اصلی: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"خطا در اجرای اصلی: {e}")
        print(f"خطا در اجرای اصلی: {e}")
    finally:
        conn.close()
        loop.close()