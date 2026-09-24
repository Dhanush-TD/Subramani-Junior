from tools.network_tools import (
    get_wifi_status,
    turn_wifi_on,
    turn_wifi_off,
)

print("Current status:")
print(get_wifi_status.invoke({}))

print("\nTurning Wi-Fi OFF:")
print(turn_wifi_off.invoke({}))

print("\nStatus after OFF:")
print(get_wifi_status.invoke({}))

print("\nTurning Wi-Fi ON:")
print(turn_wifi_on.invoke({}))

print("\nFinal status:")
print(get_wifi_status.invoke({}))