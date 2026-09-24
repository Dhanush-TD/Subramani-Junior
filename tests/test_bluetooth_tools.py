from tools.bluetooth_tools import (
    get_bluetooth_status,
    turn_bluetooth_off,
)

print("Before:")
print(get_bluetooth_status.invoke({}))

print("\nTurning Bluetooth OFF:")
print(turn_bluetooth_off.invoke({}))

print("\nAfter:")
print(get_bluetooth_status.invoke({}))