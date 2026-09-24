import asyncio

from messaging.telegram_tools import send_file


async def main():

    chat_id = "7510152015"

    file_path = r"C:\Users\dhanu\retrieved_files\ttth.txt"

    result = await send_file(
        chat_id,
        file_path
    )

    print(result)


asyncio.run(main())