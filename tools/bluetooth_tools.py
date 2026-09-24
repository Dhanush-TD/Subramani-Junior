import asyncio

from langchain_core.tools import tool
from winrt.windows.devices.radios import (
    Radio,
    RadioKind,
    RadioState,
)


async def get_bluetooth_radio():
    radios = await Radio.get_radios_async()

    for radio in radios:
        if radio.kind == RadioKind.BLUETOOTH:
            return radio

    return None


async def get_status():
    radio = await get_bluetooth_radio()

    if radio is None:
        return "Bluetooth radio not found."

    if radio.state == RadioState.ON:
        return "Bluetooth is enabled."

    if radio.state == RadioState.OFF:
        return "Bluetooth is disabled."

    if radio.state == RadioState.DISABLED:
        return "Bluetooth is disabled by hardware or system policy."

    return f"Bluetooth status is {radio.state}."


async def set_bluetooth_state(state):
    radio = await get_bluetooth_radio()

    if radio is None:
        return "Bluetooth radio not found."

    # Directly change the Bluetooth radio state.
    result = await radio.set_state_async(state)

    if state == RadioState.ON:
        if result:
            return "Bluetooth turned on successfully."

        return f"Windows could not turn Bluetooth on. Result: {result}"

    if state == RadioState.OFF:
        if result:
            return "Bluetooth turned off successfully."

        return f"Windows could not turn Bluetooth off. Result: {result}"

    return f"Bluetooth state change result: {result}"


@tool
def get_bluetooth_status():
    """
    Check the actual Windows Bluetooth radio state.
    """
    return asyncio.run(get_status())


@tool
def turn_bluetooth_on():
    """
    Turn the Windows Bluetooth radio on.
    """
    return asyncio.run(
        set_bluetooth_state(RadioState.ON)
    )


@tool
def turn_bluetooth_off():
    """
    Turn the Windows Bluetooth radio off.
    """
    return asyncio.run(
        set_bluetooth_state(RadioState.OFF)
    )