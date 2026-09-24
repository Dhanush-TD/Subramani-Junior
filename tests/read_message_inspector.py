from __future__ import annotations

import time
import ctypes
from pywinauto import Desktop


WHATSAPP_TITLE = "WhatsApp"
WHATSAPP_CLASS = "WinUIDesktopWin32WindowClass"

# Right side of WhatsApp
MESSAGE_AREA_LEFT = 500


def find_whatsapp():
    desktop = Desktop(backend="uia")

    for window in desktop.windows():
        try:
            if (
                (window.window_text() or "").strip()
                == WHATSAPP_TITLE
                and
                (window.class_name() or "").strip()
                == WHATSAPP_CLASS
            ):
                return window
        except Exception:
            pass

    return None


def focus_whatsapp(window):

    hwnd = window.handle

    try:
        ctypes.windll.user32.ShowWindow(hwnd, 9)
    except Exception:
        pass

    try:
        window.restore()
    except Exception:
        pass

    time.sleep(0.3)

    try:
        window.maximize()
    except Exception:
        pass

    time.sleep(0.5)

    try:
        window.set_focus()
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass

    time.sleep(0.5)


def inspect_current_chat(window):

    print()
    print("=" * 70)
    print("READ CURRENT CHAT")
    print("=" * 70)

    # --------------------------------------------------------
    # Get all controls
    # --------------------------------------------------------

    controls = window.descendants()

    print(
        f"[UIA] Total controls: {len(controls)}"
    )

    # --------------------------------------------------------
    # Only controls in message area
    # --------------------------------------------------------

    found = []

    for control in controls:

        try:

            if not control.is_visible():
                continue

            rect = control.rectangle()

            if rect is None:
                continue

            # Ignore left chat list
            if rect.left < MESSAGE_AREA_LEFT:
                continue

            # Ignore header
            if rect.top < 130:
                continue

            # Ignore message composer/footer
            if rect.top > 1050:
                continue

            control_type = (
                control.element_info.control_type
                or ""
            )

            name = (
                control.element_info.name
                or ""
            ).strip()

            if not name:
                continue

            if control_type not in {
                "Text",
                "DataItem",
                "ListItem",
                "Group",
                "Custom",
            }:
                continue

            found.append(
                (
                    rect.top,
                    rect.left,
                    control_type,
                    name,
                    rect,
                    control,
                )
            )

        except Exception:
            continue

    # --------------------------------------------------------
    # Sort top -> bottom
    # --------------------------------------------------------

    found.sort(
        key=lambda x: (
            x[0],
            x[1],
        )
    )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    seen = set()

    unique = []

    for item in found:

        (
            top,
            left,
            control_type,
            name,
            rect,
            control,
        ) = item

        key = (
            control_type,
            name,
            rect.left,
            rect.top,
            rect.right,
            rect.bottom,
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(item)

    # --------------------------------------------------------
    # Print only first 150
    # --------------------------------------------------------

    print()
    print(
        f"[READ] Relevant controls: {len(unique)}"
    )

    print()

    for index, item in enumerate(
        unique[:150],
        start=1
    ):

        (
            top,
            left,
            control_type,
            name,
            rect,
            control,
        ) = item

        print(
            f"[{index}] "
            f"{control_type:<10} "
            f"{name!r}"
        )

        print(
            f"     Rect: {rect}"
        )

    print()
    print("=" * 70)


def main():

    print()
    print("=" * 70)
    print("WHATSAPP SPECIFIC CHAT MESSAGE TEST")
    print("=" * 70)

    whatsapp = find_whatsapp()

    if whatsapp is None:

        print(
            "ERROR: WhatsApp not found."
        )

        return

    print(
        "[WINDOW] WhatsApp found"
    )

    focus_whatsapp(
        whatsapp
    )

    print(
        "[WINDOW] WhatsApp focused"
    )

    print()
    print(
        "[INFO] Leave WhatsApp on the chat you want to read."
    )

    print(
        "[INFO] Reading only the right-side message area."
    )

    inspect_current_chat(
        whatsapp
    )


if __name__ == "__main__":
    main()