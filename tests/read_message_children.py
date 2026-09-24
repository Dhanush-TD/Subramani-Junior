from __future__ import annotations

import ctypes
import sys
import time

from pywinauto import Desktop


# ============================================================
# CONFIG
# ============================================================

WHATSAPP_TITLE = "WhatsApp"
WHATSAPP_CLASS = "WinUIDesktopWin32WindowClass"

# Only visible controls
VISIBLE_ONLY = True


# ============================================================
# UTF-8
# ============================================================

try:
    sys.stdout.reconfigure(
        encoding="utf-8"
    )
except Exception:
    pass


# ============================================================
# FIND WHATSAPP
# ============================================================

def find_whatsapp():

    desktop = Desktop(
        backend="uia"
    )

    print(
        "[WINDOW] Searching for WhatsApp...",
        flush=True
    )

    for window in desktop.windows():

        try:

            title = (
                window.window_text()
                or ""
            ).strip()

            class_name = (
                window.class_name()
                or ""
            ).strip()

            if (
                title == WHATSAPP_TITLE
                and
                class_name == WHATSAPP_CLASS
            ):

                print(
                    "[WINDOW] WhatsApp found",
                    flush=True
                )

                return window

        except Exception:
            continue

    return None


# ============================================================
# FOCUS WHATSAPP
# ============================================================

def focus_whatsapp(window):

    print(
        "[WINDOW] Preparing WhatsApp...",
        flush=True
    )

    hwnd = window.handle

    try:
        ctypes.windll.user32.ShowWindow(
            hwnd,
            9
        )
    except Exception:
        pass

    try:
        window.restore()
    except Exception:
        pass

    time.sleep(0.3)

    try:
        window.maximize()

        print(
            "[WINDOW] Maximized",
            flush=True
        )

    except Exception:
        pass

    time.sleep(0.5)

    try:
        window.set_focus()
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetForegroundWindow(
            hwnd
        )
    except Exception:
        pass

    time.sleep(0.5)

    print(
        "[WINDOW] WhatsApp focused",
        flush=True
    )


# ============================================================
# INSPECT EVERYTHING VISIBLE
# ============================================================

def inspect_screen(window):

    print()
    print("=" * 90)
    print("WHATSAPP FULL VISIBLE UI INSPECTION")
    print("=" * 90)

    print()
    print(
        "[UIA] Reading complete WhatsApp UI tree...",
        flush=True
    )

    start = time.time()

    try:

        controls = window.descendants()

    except Exception as exc:

        print(
            f"[ERROR] Could not read UI tree: {exc}"
        )

        return

    elapsed = time.time() - start

    print(
        f"[UIA] Total controls: "
        f"{len(controls)}",
        flush=True
    )

    print(
        f"[UIA] Read time: "
        f"{elapsed:.2f}s",
        flush=True
    )

    # ========================================================
    # COLLECT VISIBLE NON-EMPTY
    # ========================================================

    results = []

    for control in controls:

        try:

            if VISIBLE_ONLY:

                if not control.is_visible():
                    continue

            info = control.element_info

            name = (
                info.name
                or ""
            ).strip()

            automation_id = (
                info.automation_id
                or ""
            ).strip()

            class_name = (
                info.class_name
                or ""
            ).strip()

            control_type = (
                info.control_type
                or ""
            ).strip()

            try:
                help_text = (
                    info.help_text
                    or ""
                ).strip()
            except Exception:
                help_text = ""

            rect = control.rectangle()

            if rect is None:
                continue

            # ------------------------------------------------
            # Keep anything that contains useful information.
            # ------------------------------------------------

            if (
                not name
                and
                not automation_id
                and
                not class_name
                and
                not help_text
            ):
                continue

            results.append(
                (
                    rect.top,
                    rect.left,
                    control_type,
                    name,
                    automation_id,
                    class_name,
                    help_text,
                    rect,
                    control,
                )
            )

        except Exception:
            continue

    # ========================================================
    # SORT BY SCREEN POSITION
    # ========================================================

    results.sort(
        key=lambda x: (
            x[0],
            x[1],
        )
    )

    print()
    print(
        f"[UIA] Visible non-empty controls: "
        f"{len(results)}",
        flush=True
    )

    # ========================================================
    # DEDUPLICATE
    # ========================================================

    unique = []

    seen = set()

    for item in results:

        (
            top,
            left,
            control_type,
            name,
            automation_id,
            class_name,
            help_text,
            rect,
            control,
        ) = item

        key = (
            control_type,
            name,
            automation_id,
            class_name,
            help_text,
            rect.left,
            rect.top,
            rect.right,
            rect.bottom,
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(item)

    print(
        f"[UIA] Unique visible controls: "
        f"{len(unique)}",
        flush=True
    )

    # ========================================================
    # PRINT EVERYTHING
    # ========================================================

    print()
    print("=" * 90)
    print("VISIBLE UI ELEMENTS")
    print("=" * 90)

    for index, item in enumerate(
        unique,
        start=1
    ):

        (
            top,
            left,
            control_type,
            name,
            automation_id,
            class_name,
            help_text,
            rect,
            control,
        ) = item

        print()
        print(
            f"[{index}]"
        )

        print(
            f"  Type          : {control_type}"
        )

        print(
            f"  Name          : {name!r}"
        )

        print(
            f"  Automation ID : {automation_id!r}"
        )

        print(
            f"  Class         : {class_name!r}"
        )

        if help_text:

            print(
                f"  Help Text     : {help_text!r}"
            )

        print(
            f"  Rectangle     : {rect}"
        )

        try:

            print(
                f"  Handle        : "
                f"{control.handle}"
            )

        except Exception:
            pass

    # ========================================================
    # MESSAGE-LOOKING TEXT
    # ========================================================

    print()
    print("=" * 90)
    print("TEXT-LIKE ELEMENTS IN MAIN CHAT AREA")
    print("=" * 90)

    count = 0

    for item in unique:

        (
            top,
            left,
            control_type,
            name,
            automation_id,
            class_name,
            help_text,
            rect,
            control,
        ) = item

        # ----------------------------------------------------
        # Main chat area
        # ----------------------------------------------------

        if rect.left < 500:
            continue

        if rect.top < 130:
            continue

        if rect.top > 1050:
            continue

        # ----------------------------------------------------
        # Anything with actual text/name
        # ----------------------------------------------------

        if not name:
            continue

        count += 1

        print()
        print(
            f"[{count}] "
            f"{control_type}"
        )

        print(
            f"  Text      : {name!r}"
        )

        print(
            f"  Rectangle : {rect}"
        )

        print(
            f"  Class     : {class_name!r}"
        )

        print(
            f"  Automation: {automation_id!r}"
        )

    print()
    print("=" * 90)
    print(
        f"MAIN CHAT TEXT ELEMENTS: {count}"
    )
    print("=" * 90)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 90)
    print("WHATSAPP SCREEN INSPECTOR")
    print("=" * 90)

    window = find_whatsapp()

    if window is None:

        print(
            "[ERROR] WhatsApp not found."
        )

        return

    focus_whatsapp(
        window
    )

    print()
    print(
        "[INFO] Leave the desired chat open."
    )

    print(
        "[INFO] Do not click anything while inspection runs."
    )

    time.sleep(0.5)

    inspect_screen(
        window
    )


if __name__ == "__main__":

    main()