from __future__ import annotations

import sys
import time
import ctypes

from pywinauto import Desktop


# ============================================================
# UTF-8 OUTPUT
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# CONFIG
# ============================================================

WHATSAPP_TITLE = "WhatsApp"
WHATSAPP_CLASS = "WinUIDesktopWin32WindowClass"

# How long to wait for WhatsApp
TIMEOUT = 8.0

# Only inspect this much of the lower part of WhatsApp.
# This keeps the output small.
BOTTOM_AREA_RATIO = 0.72


# ============================================================
# WINDOW HELPERS
# ============================================================

def find_whatsapp():
    """
    Find the real WhatsApp Desktop window.
    """

    desktop = Desktop(backend="uia")

    print("[WINDOW] Searching for WhatsApp...", flush=True)

    deadline = time.time() + TIMEOUT

    while time.time() < deadline:

        try:
            windows = desktop.windows()

            for window in windows:

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

        except Exception:
            pass

        time.sleep(0.25)

    return None


def force_foreground(window):
    """
    Restore, maximize and foreground WhatsApp.

    This is important because WhatsApp may be minimized.
    """

    hwnd = window.handle

    print(
        f"[WINDOW] Handle: {hwnd}",
        flush=True
    )

    # --------------------------------------------------------
    # SW_RESTORE
    # --------------------------------------------------------

    try:
        ctypes.windll.user32.ShowWindow(
            hwnd,
            9
        )
    except Exception:
        pass

    time.sleep(0.3)

    # --------------------------------------------------------
    # Bring to foreground
    # --------------------------------------------------------

    try:
        ctypes.windll.user32.SetForegroundWindow(
            hwnd
        )
    except Exception:
        pass

    time.sleep(0.3)

    # --------------------------------------------------------
    # pywinauto restore
    # --------------------------------------------------------

    try:
        window.restore()
    except Exception:
        pass

    time.sleep(0.3)

    # --------------------------------------------------------
    # Maximize
    # --------------------------------------------------------

    try:
        window.maximize()

        print(
            "[WINDOW] WhatsApp maximized",
            flush=True
        )

    except Exception as exc:

        print(
            f"[WINDOW] Maximize warning: {exc}",
            flush=True
        )

    time.sleep(0.5)

    # --------------------------------------------------------
    # Focus
    # --------------------------------------------------------

    try:
        window.set_focus()

        print(
            "[WINDOW] WhatsApp focused",
            flush=True
        )

    except Exception:

        try:
            ctypes.windll.user32.SetForegroundWindow(
                hwnd
            )
        except Exception:
            pass

    time.sleep(0.5)


# ============================================================
# RECTANGLE HELPERS
# ============================================================

def rect_info(rect):
    """
    Convert pywinauto rectangle to readable information.
    """

    return (
        f"L={rect.left}, "
        f"T={rect.top}, "
        f"R={rect.right}, "
        f"B={rect.bottom}, "
        f"W={rect.width()}, "
        f"H={rect.height()}"
    )


def is_bottom_area(rect, window_rect):
    """
    Return True if control is in the lower portion
    of the WhatsApp window.
    """

    window_height = (
        window_rect.bottom
        -
        window_rect.top
    )

    relative_top = (
        rect.top
        -
        window_rect.top
    )

    return (
        relative_top
        >=
        window_height * BOTTOM_AREA_RATIO
    )


# ============================================================
# INSPECT BUTTONS
# ============================================================

def inspect_bottom_buttons(whatsapp):
    """
    Inspect only buttons in the lower part of WhatsApp.

    This is deliberately NOT a full UI tree dump.
    """

    print()
    print("=" * 70)
    print("WHATSAPP ATTACHMENT BUTTON INSPECTION")
    print("=" * 70)

    try:
        window_rect = whatsapp.rectangle()

    except Exception as exc:

        print(
            f"[ERROR] Could not get WhatsApp rectangle: {exc}",
            flush=True
        )

        return

    print()
    print(
        f"[WINDOW] {rect_info(window_rect)}",
        flush=True
    )

    # --------------------------------------------------------
    # Get buttons
    # --------------------------------------------------------

    try:

        buttons = whatsapp.descendants(
            control_type="Button"
        )

    except Exception as exc:

        print(
            f"[ERROR] Could not inspect buttons: {exc}",
            flush=True
        )

        return

    candidates = []

    for button in buttons:

        try:

            if not button.is_visible():
                continue

            rect = button.rectangle()

            if rect is None:
                continue

            # ------------------------------------------------
            # Must be inside WhatsApp
            # ------------------------------------------------

            if rect.left < window_rect.left:
                continue

            if rect.right > window_rect.right:
                continue

            # ------------------------------------------------
            # Only lower part
            # ------------------------------------------------

            if not is_bottom_area(
                rect,
                window_rect
            ):
                continue

            # ------------------------------------------------
            # Accessibility information
            # ------------------------------------------------

            try:
                name = (
                    button.element_info.name
                    or ""
                ).strip()
            except Exception:
                name = ""

            try:
                automation_id = (
                    button.element_info.automation_id
                    or ""
                ).strip()
            except Exception:
                automation_id = ""

            try:
                control_type = (
                    button.element_info.control_type
                    or ""
                )
            except Exception:
                control_type = ""

            try:
                class_name = (
                    button.element_info.class_name
                    or ""
                ).strip()
            except Exception:
                class_name = ""

            try:
                help_text = (
                    button.element_info.help_text
                    or ""
                ).strip()
            except Exception:
                help_text = ""

            # ------------------------------------------------
            # Relative position
            # ------------------------------------------------

            relative_x = (
                rect.left
                -
                window_rect.left
            )

            relative_y = (
                rect.top
                -
                window_rect.top
            )

            candidates.append(
                {
                    "button": button,
                    "name": name,
                    "automation_id": automation_id,
                    "control_type": control_type,
                    "class_name": class_name,
                    "help_text": help_text,
                    "rect": rect,
                    "relative_x": relative_x,
                    "relative_y": relative_y,
                }
            )

        except Exception:
            continue

    # --------------------------------------------------------
    # Sort:
    #
    # top -> bottom
    # left -> right
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item: (
            item["rect"].top,
            item["rect"].left
        )
    )

    print()
    print(
        f"[RESULT] Bottom-area buttons found: "
        f"{len(candidates)}",
        flush=True
    )

    print()

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    for index, item in enumerate(
        candidates,
        start=1
    ):

        print(
            "-" * 70
        )

        print(
            f"BUTTON #{index}"
        )

        print(
            f"Name          : "
            f"{item['name']!r}"
        )

        print(
            f"AutomationId  : "
            f"{item['automation_id']!r}"
        )

        print(
            f"ControlType   : "
            f"{item['control_type']!r}"
        )

        print(
            f"ClassName     : "
            f"{item['class_name']!r}"
        )

        print(
            f"HelpText      : "
            f"{item['help_text']!r}"
        )

        print(
            f"Rectangle     : "
            f"{rect_info(item['rect'])}"
        )

        print(
            f"Relative X    : "
            f"{item['relative_x']}"
        )

        print(
            f"Relative Y    : "
            f"{item['relative_y']}"
        )

    # ========================================================
    # POSSIBLE PLUS CANDIDATES
    # ========================================================

    print()
    print("=" * 70)
    print("POSSIBLE '+' BUTTONS")
    print("=" * 70)

    plus_candidates = []

    for item in candidates:

        name = item["name"].casefold()

        automation_id = (
            item["automation_id"]
            .casefold()
        )

        help_text = (
            item["help_text"]
            .casefold()
        )

        combined = (
            f"{name} "
            f"{automation_id} "
            f"{help_text}"
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Do NOT treat "attach" or "add" alone as +.
        #
        # "Remove attachment" contains "attachment"
        # and caused the previous implementation to select
        # the WRONG button.
        # ----------------------------------------------------

        strong_keywords = (
            "plus",
            "add attachment",
            "add file",
            "add files",
        )

        if any(
            keyword in combined
            for keyword in strong_keywords
        ):
            plus_candidates.append(item)

    # --------------------------------------------------------
    # If accessibility gives no useful name,
    # identify small buttons by geometry.
    # --------------------------------------------------------

    if not plus_candidates:

        for item in candidates:

            rect = item["rect"]

            width = rect.width()
            height = rect.height()

            relative_x = item["relative_x"]

            window_width = (
                window_rect.right
                -
                window_rect.left
            )

            # ------------------------------------------------
            # Small button
            # ------------------------------------------------

            if width > 80:
                continue

            if height > 80:
                continue

            # ------------------------------------------------
            # Not far-right.
            #
            # Send button is normally at far right.
            # ------------------------------------------------

            if relative_x > (
                window_width * 0.80
            ):
                continue

            plus_candidates.append(item)

    # --------------------------------------------------------
    # Print possible + candidates
    # --------------------------------------------------------

    if not plus_candidates:

        print(
            "No obvious '+' candidate found."
        )

    else:

        for index, item in enumerate(
            plus_candidates,
            start=1
        ):

            print()
            print(
                f"CANDIDATE #{index}"
            )

            print(
                f"Name         : "
                f"{item['name']!r}"
            )

            print(
                f"AutomationId : "
                f"{item['automation_id']!r}"
            )

            print(
                f"ControlType  : "
                f"{item['control_type']!r}"
            )

            print(
                f"ClassName    : "
                f"{item['class_name']!r}"
            )

            print(
                f"Rectangle    : "
                f"{rect_info(item['rect'])}"
            )

    # ========================================================
    # SEND BUTTON CANDIDATES
    # ========================================================

    print()
    print("=" * 70)
    print("POSSIBLE SEND BUTTONS")
    print("=" * 70)

    send_candidates = []

    for item in candidates:

        name = item["name"].casefold()

        automation_id = (
            item["automation_id"]
            .casefold()
        )

        help_text = (
            item["help_text"]
            .casefold()
        )

        combined = (
            f"{name} "
            f"{automation_id} "
            f"{help_text}"
        )

        if "send" in combined:

            send_candidates.append(item)

    if not send_candidates:

        print(
            "No accessibility-labelled Send button found."
        )

    else:

        for index, item in enumerate(
            send_candidates,
            start=1
        ):

            print()
            print(
                f"SEND CANDIDATE #{index}"
            )

            print(
                f"Name         : "
                f"{item['name']!r}"
            )

            print(
                f"AutomationId : "
                f"{item['automation_id']!r}"
            )

            print(
                f"ControlType  : "
                f"{item['control_type']!r}"
            )

            print(
                f"ClassName    : "
                f"{item['class_name']!r}"
            )

            print(
                f"Rectangle    : "
                f"{rect_info(item['rect'])}"
            )

    print()
    print("=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def inspect_attachment_page():

    print()
    print("=" * 70)
    print("WHATSAPP ATTACHMENT PAGE INSPECTOR")
    print("=" * 70)

    # --------------------------------------------------------
    # Find WhatsApp
    # --------------------------------------------------------

    whatsapp = find_whatsapp()

    if whatsapp is None:

        print(
            "[ERROR] WhatsApp Desktop was not found."
        )

        return

    # --------------------------------------------------------
    # Automatically restore/focus/maximize
    # --------------------------------------------------------

    force_foreground(
        whatsapp
    )

    # --------------------------------------------------------
    # Inspect current page
    # --------------------------------------------------------

    inspect_bottom_buttons(
        whatsapp
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    inspect_attachment_page()