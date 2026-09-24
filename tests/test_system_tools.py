from tools.system_tools import (
    get_volume,
    set_volume,
    increase_volume,
    decrease_volume,
    mute_volume,
    unmute_volume
)


print(
    get_volume.invoke({})
)

print(
    set_volume.invoke({
        "level": 50
    })
)

print(
    get_volume.invoke({})
)

print(
    increase_volume.invoke({
        "amount": 5
    })
)

print(
    decrease_volume.invoke({
        "amount": 5
    })
)

print(
    mute_volume.invoke({})
)

print(
    unmute_volume.invoke({})
)