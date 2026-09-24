import screen_brightness_control as sbc

from langchain_core.tools import tool


# =========================================================
# GET BRIGHTNESS
# =========================================================

@tool
def get_brightness():
    """
    Get the current screen brightness percentage.
    """

    brightness = sbc.get_brightness()

    if not brightness:
        return "Could not determine brightness."

    level = round(
        sum(brightness) / len(brightness)
    )

    return f"Current brightness is {level}%."


# =========================================================
# SET BRIGHTNESS
# =========================================================

@tool
def set_brightness(level: int):
    """
    Set screen brightness from 0 to 100 percent.
    """

    if level < 0 or level > 100:
        return "Brightness must be between 0 and 100."

    sbc.set_brightness(level)

    return f"Brightness set to {level}%."


# =========================================================
# INCREASE BRIGHTNESS
# =========================================================

@tool
def increase_brightness(amount: int = 10):
    """
    Increase screen brightness.

    Default increase is 10%.
    """

    brightness = sbc.get_brightness()

    if not brightness:
        return "Could not determine current brightness."

    current = round(
        sum(brightness) / len(brightness)
    )

    new_level = min(
        current + amount,
        100
    )

    sbc.set_brightness(new_level)

    return (
        f"Brightness increased from "
        f"{current}% to {new_level}%."
    )


# =========================================================
# DECREASE BRIGHTNESS
# =========================================================

@tool
def decrease_brightness(amount: int = 10):
    """
    Decrease screen brightness.

    Default decrease is 10%.
    """

    brightness = sbc.get_brightness()

    if not brightness:
        return "Could not determine current brightness."

    current = round(
        sum(brightness) / len(brightness)
    )

    new_level = max(
        current - amount,
        0
    )

    sbc.set_brightness(new_level)

    return (
        f"Brightness decreased from "
        f"{current}% to {new_level}%."
    )