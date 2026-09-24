import os
import asyncio

from dotenv import load_dotenv
from telegram import Bot


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def main():

    bot = Bot(token=TOKEN)

    webhook = await bot.get_webhook_info()

    print("Webhook URL:", webhook.url)
    print("Pending updates:", webhook.pending_update_count)

    updates = await bot.get_updates()

    print("\nUpdates received:", len(updates))

    for update in updates:

        if update.message:

            print("Chat ID:", update.message.chat.id)
            print("Username:", update.message.chat.username)
            print("Message:", update.message.text)


asyncio.run(main())