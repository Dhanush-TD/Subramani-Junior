from pycaw.pycaw import AudioUtilities
from langchain_core.tools import tool
# =========================================================
# GET VOLUME INTERFACE
# =========================================================

def get_volume_interface():

    devices = AudioUtilities.GetSpeakers()

    volume = devices.EndpointVolume

    return volume


# =========================================================
# GET CURRENT VOLUME
# =========================================================

@tool
def get_volume():
    """
    Get the current Windows system volume percentage.
    """

    volume = get_volume_interface()

    current = volume.GetMasterVolumeLevelScalar()

    percentage = round(current * 100)

    return f"Current volume is {percentage}%."


# =========================================================
# SET VOLUME
# =========================================================

@tool
def set_volume(level: int):
    """
    Set Windows system volume to a percentage from 0 to 100.
    """

    if level < 0 or level > 100:
        return "Volume must be between 0 and 100."

    volume = get_volume_interface()

    volume.SetMasterVolumeLevelScalar(
        level / 100,
        None
    )

    return f"Volume set to {level}%."


# =========================================================
# INCREASE VOLUME
# =========================================================

@tool
def increase_volume(amount: int = 10):
    """
    Increase Windows system volume.

    Default increase is 10%.
    """

    volume = get_volume_interface()

    current = volume.GetMasterVolumeLevelScalar()

    current_level = round(current * 100)

    new_level = min(
        current_level + amount,
        100
    )

    volume.SetMasterVolumeLevelScalar(
        new_level / 100,
        None
    )

    return (
        f"Volume increased from "
        f"{current_level}% to {new_level}%."
    )


# =========================================================
# DECREASE VOLUME
# =========================================================

@tool
def decrease_volume(amount: int = 10):
    """
    Decrease Windows system volume.

    Default decrease is 10%.
    """

    volume = get_volume_interface()

    current = volume.GetMasterVolumeLevelScalar()

    current_level = round(current * 100)

    new_level = max(
        current_level - amount,
        0
    )

    volume.SetMasterVolumeLevelScalar(
        new_level / 100,
        None
    )

    return (
        f"Volume decreased from "
        f"{current_level}% to {new_level}%."
    )


# =========================================================
# MUTE
# =========================================================

@tool
def mute_volume():
    """
    Mute Windows system volume.
    """

    volume = get_volume_interface()

    volume.SetMute(
        1,
        None
    )

    return "Volume muted."


# =========================================================
# UNMUTE
# =========================================================

@tool
def unmute_volume():
    """
    Unmute Windows system volume.
    """

    volume = get_volume_interface()

    volume.SetMute(
        0,
        None
    )

    return "Volume unmuted."