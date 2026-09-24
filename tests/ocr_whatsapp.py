from __future__ import annotations

import ctypes
import os
import sys
import time

import pyautogui
import pytesseract
from PIL import Image


# ============================================================
# CONFIG
# ============================================================

WHATSAPP_TITLE = "WhatsApp"

# Tesseract path
# Change this only if your installation is elsewhere.
TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# WhatsApp chat area
#
# Based on our previous UI inspection:
#
# Left   ~555
# Top    ~127
# Right  ~1907
# Bottom ~1060
#
CHAT_REGION = (
    555,     # left
    127,     # top
    1352,    # width
    933      # height
)


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
# FIND WHATSAPP WINDOW
# ============================================================

def find_whatsapp():

    from pywinauto import Desktop

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
                class_name
                == "WinUIDesktopWin32WindowClass"
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
        "[WINDOW] Focusing WhatsApp...",
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

    time.sleep(0.3)

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
# CHECK TESSERACT
# ============================================================

def check_tesseract():

    if os.path.isfile(
        TESSERACT_PATH
    ):

        pytesseract.pytesseract.tesseract_cmd = (
            TESSERACT_PATH
        )

        print(
            "[OCR] Tesseract found",
            flush=True
        )

        return True

    # Try PATH
    try:

        version = (
            pytesseract.get_tesseract_version()
        )

        print(
            f"[OCR] Tesseract found: "
            f"{version}",
            flush=True
        )

        return True

    except Exception:

        print()
        print(
            "[OCR] Tesseract was not found."
        )

        print(
            f"[OCR] Expected:"
        )

        print(
            f"      {TESSERACT_PATH}"
        )

        print()
        print(
            "Install Tesseract OCR first."
        )

        return False


# ============================================================
# TAKE CHAT SCREENSHOT
# ============================================================

def capture_chat():

    print(
        "[SCREENSHOT] Capturing WhatsApp chat area...",
        flush=True
    )

    screenshot = pyautogui.screenshot(
        region=CHAT_REGION
    )

    print(
        "[SCREENSHOT] Captured",
        flush=True
    )

    # Save it so we can visually inspect it.
    output_path = (
        "tests/whatsapp_chat.png"
    )

    screenshot.save(
        output_path
    )

    print(
        f"[SCREENSHOT] Saved: "
        f"{output_path}",
        flush=True
    )

    return screenshot


# ============================================================
# OCR
# ============================================================

def run_ocr(image):

    print(
        "[OCR] Running OCR...",
        flush=True
    )

    start = time.time()

    text = pytesseract.image_to_string(
        image,
        lang="eng",
        config="--psm 6"
    )

    elapsed = (
        time.time()
        - start
    )

    print(
        f"[OCR] Completed in "
        f"{elapsed:.2f} seconds",
        flush=True
    )

    return text


# ============================================================
# PRINT OCR RESULT
# ============================================================

def print_result(text):

    print()
    print("=" * 80)
    print("OCR RESULT")
    print("=" * 80)

    if not text.strip():

        print(
            "No text detected."
        )

    else:

        print(
            text.strip()
        )

    print("=" * 80)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("WHATSAPP OCR TEST")
    print("=" * 80)

    # --------------------------------------------------------
    # Tesseract
    # --------------------------------------------------------

    if not check_tesseract():

        return

    # --------------------------------------------------------
    # WhatsApp
    # --------------------------------------------------------

    whatsapp = find_whatsapp()

    if whatsapp is None:

        print(
            "[ERROR] WhatsApp not found."
        )

        return

    # --------------------------------------------------------
    # Focus
    # --------------------------------------------------------

    focus_whatsapp(
        whatsapp
    )

    # Give WhatsApp time to render
    time.sleep(0.5)

    # --------------------------------------------------------
    # Capture
    # --------------------------------------------------------

    image = capture_chat()

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    text = run_ocr(
        image
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    print_result(
        text
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()