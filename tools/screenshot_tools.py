import os
from datetime import datetime

from PIL import ImageGrab
from langchain_core.tools import tool


@tool
def take_screenshot():
    """
    Take a screenshot of the entire screen and save it to the Desktop.
    """

    try:
        desktop = os.path.join(
            os.path.expanduser("~"),
            "Desktop"
        )

        os.makedirs(desktop, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filepath = os.path.join(
            desktop,
            f"Screenshot_{timestamp}.png"
        )

        screenshot = ImageGrab.grab()
        screenshot.save(filepath)

        return f"Screenshot saved successfully: {filepath}"

    except Exception as e:
        return f"Could not take screenshot: {e}"