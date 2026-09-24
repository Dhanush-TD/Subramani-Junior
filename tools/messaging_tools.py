from langchain_core.tools import tool

from messaging.telegram_tools import (
    send_message as telegram_send_message,
    send_file as telegram_send_file
)


# =========================================================
# SEND TELEGRAM MESSAGE
# =========================================================

@tool
def send_message(message: str):
    """
    Send a text message to the configured Telegram chat.
    """

    try:

        result = telegram_send_message(
            message
        )

        return result

    except Exception as e:

        return (
            f"Failed to send Telegram message: "
            f"{e}"
        )


# =========================================================
# SEND TELEGRAM FILE
# =========================================================

@tool
def send_file(file_path: str):
    """
    Send a file to the configured Telegram chat.
    """

    try:

        result = telegram_send_file(
            file_path
        )

        return result

    except Exception as e:

        return (
            f"Failed to send Telegram file: "
            f"{e}"
        )