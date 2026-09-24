import subprocess

from langchain_core.tools import tool


WIFI_INTERFACE = "Wi-Fi"


def run_netsh_command(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=True
    )

    if result.returncode != 0:
        return result.stderr.strip()

    return result.stdout.strip()


# =========================================================
# WI-FI STATUS
# =========================================================

@tool
def get_wifi_status():
    """
    Check whether the Windows Wi-Fi adapter is enabled.
    """

    output = run_netsh_command(
        f'netsh interface show interface name="{WIFI_INTERFACE}"'
    )

    if not output:
        return "Could not determine Wi-Fi status."

    if "Enabled" in output:
        return "Wi-Fi is enabled."

    if "Disabled" in output:
        return "Wi-Fi is disabled."

    return output


# =========================================================
# TURN WI-FI ON
# =========================================================

@tool
def turn_wifi_on():
    """
    Turn the Windows Wi-Fi adapter on.
    """

    output = run_netsh_command(
        f'netsh interface set interface name="{WIFI_INTERFACE}" admin=enabled'
    )

    if "Ok." in output or output == "":
        return "Wi-Fi turned on successfully."

    return f"Could not turn Wi-Fi on: {output}"


# =========================================================
# TURN WI-FI OFF
# =========================================================

@tool
def turn_wifi_off():
    """
    Turn the Windows Wi-Fi adapter off.
    """

    output = run_netsh_command(
        f'netsh interface set interface name="{WIFI_INTERFACE}" admin=disabled'
    )

    if "Ok." in output or output == "":
        return "Wi-Fi turned off successfully."

    return f"Could not turn Wi-Fi off: {output}"