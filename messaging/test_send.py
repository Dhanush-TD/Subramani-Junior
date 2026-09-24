import asyncio

from messaging.telegram_tools import send_message


async def main():

    chat_id = "7510152015"

    result = await send_message(
        chat_id,
        "Hello from my AI agent!"
    )

    print(result)


asyncio.run(main())