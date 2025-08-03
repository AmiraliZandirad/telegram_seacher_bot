import asyncio
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
import httpx

api_id = 25517812
api_hash = "1651908df3a7fb05ba65905ae0d32bc0"
session_name = "car_user"
bot_token = "8242002160:AAGDtD14wUI4EajkKnBDixqnUwDQXAhBtKE"

AI_API_URL = "https://api.avalai.ir/v1/extract-car-info"
AI_API_TOKEN = "aa-i65SVPZOrRHLjqR8RhXVRiAu61KD7rbgONplPMxem76igylU"

async def extract_info_with_ai(text: str):
    headers = {
        "Authorization": f"Bearer {AI_API_TOKEN}",
        "Content-Type": "application/json"
    }
    json_data = {"text": text}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(AI_API_URL, json=json_data, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"AI API error: {e}")
            return None

async def search_car_price(query: str):
    results = []
    async with Client(session_name, api_id=api_id, api_hash=api_hash) as app:
        async for dialog in app.get_dialogs():
            if dialog.chat.type == "channel":
                username = dialog.chat.username
                if not username:
                    continue
                try:
                    async for msg in app.search_messages(username, query, limit=50):
                        if msg.text:
                            ai_result = await extract_info_with_ai(msg.text)
                            if ai_result and "price" in ai_result and "car_name" in ai_result:
                                price = ai_result["price"]
                                car_name = ai_result["car_name"]
                                results.append((price, car_name, msg.text[:100], username, msg.message_id))
                except Exception as e:
                    print(f"Error searching messages in {username}: {e}")

    if results:
        results.sort(key=lambda x: x[0])
        price, car_name, text, channel, msg_id = results[0]
        return f"🚗 ماشین: {car_name}\n💰 کمترین قیمت: {price} تومان\n📄 متن: {text}\n🔗 https://t.me/{channel}/{msg_id}"
    else:
        return "❗ هیچ نتیجه‌ای پیدا نشد."

async def handle_message(client, message):
    query = message.text
    result = await search_car_price(query)
    await message.reply_text(result)

async def main():
    app = Client(session_name, api_id=api_id, api_hash=api_hash, bot_token=bot_token)
    await app.start()
    app.add_handler(MessageHandler(handle_message, filters.text & ~filters.command()))
    print("✅ ربات با موفقیت اجرا شد.")
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())
