from tools.brightness_tools import (
    get_brightness,
    set_brightness,
    increase_brightness,
    decrease_brightness
)


print(
    get_brightness.invoke({})
)

print(
    set_brightness.invoke({
        "level": 50
    })
)

print(
    get_brightness.invoke({})
)

print(
    increase_brightness.invoke({
        "amount": 5
    })
)

print(
    decrease_brightness.invoke({
        "amount": 5
    })
)

print(
    get_brightness.invoke({})
)