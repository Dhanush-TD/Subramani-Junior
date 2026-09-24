import os
import requests

from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# =========================================================
# SEND MESSAGE
# =========================================================

def send_message(message: str):

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        }
    )

    response.raise_for_status()

    data = response.json()

    message_id = data["result"]["message_id"]

    return (
        f"Telegram message sent successfully. "
        f"Message ID: {message_id}"
    )


# =========================================================
# SEND FILE
# =========================================================

def send_file(file_path: str):

    if not os.path.isfile(file_path):
        return f"File not found: {file_path}"

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendDocument"
    )

    with open(
        file_path,
        "rb"
    ) as file:

        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID
            },
            files={
                "document": file
            }
        )

    response.raise_for_status()

    data = response.json()

    message_id = data["result"]["message_id"]

    return (
        f"Telegram file sent successfully. "
        f"Message ID: {message_id}"
    )