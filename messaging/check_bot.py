import os
import asyncio

from dotenv import load_dotenv
from telegram import Bot


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def main():

    print("Token loaded:", bool(TOKEN))

    bot = Bot(token=TOKEN)

    me = await bot.get_me()

    print("Bot ID:", me.id)
    print("Bot username:", me.username)
    print("Bot name:", me.first_name)


asyncio.run(main())