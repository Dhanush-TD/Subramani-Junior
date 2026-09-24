from __future__ import annotations

import ctypes
import os
import re
import sys
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional, Union

import pyperclip
import pyautogui
import pytesseract
from PIL import ImageOps, ImageFilter
from pywinauto import Desktop
from pywinauto.keyboard import send_keys


# ============================================================
# CONFIGURATION
# ============================================================

WHATSAPP_TITLE = "WhatsApp"
WHATSAPP_CLASS = "WinUIDesktopWin32WindowClass"
VSCODE_CLASS = "Chrome_WidgetWin_1"

# WhatsApp search Edit control found from UI inspection
SEARCH_AUTOMATION_ID = "_r_b_"

TIMEOUT = 8.0
POLL_INTERVAL = 0.25

# Main WhatsApp content starts roughly after the left chat panel.
RIGHT_PANEL_MIN_LEFT = 430

# Tesseract installation. If Tesseract is not in PATH, use the
# standard Windows installation path used on this machine.
TESSERACT_DEFAULT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.isfile(TESSERACT_DEFAULT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_DEFAULT_PATH

# OCR screenshot output.
OCR_SCREENSHOT_PATH = Path("tests") / "whatsapp_chat.png"

# Keep console output safe on Windows PowerShell/cmd.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# ============================================================
# EXCEPTIONS
# ============================================================

class ContactNotFound(Exception):
    def __init__(self, requested: str):
        self.requested = requested
        super().__init__(
            f"No contact or chat found for '{requested}'."
        )


class ContactAmbiguous(Exception):
    def __init__(self, requested: str, matches: list[str]):
        self.requested = requested
        self.matches = matches
        super().__init__(
            f"Multiple contacts/chats match '{requested}'."
        )


class ChatVerificationFailed(Exception):
    pass


class UserCancelled(Exception):
    pass


# ============================================================
# CHAT / CONTACT RESULT
# ============================================================

@dataclass
class ChatResult:
    name: str
    raw_name: str
    element: object
    rect: object
    section: str


# ============================================================
# WHATSAPP CONNECTION
# ============================================================

class WhatsAppConnection:

    def __init__(self):
        self.desktop = Desktop(backend="uia")
        self.window = None

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    def connect(self) -> bool:
        print("[WINDOW] Searching for WhatsApp...", flush=True)

        try:
            windows = self.desktop.windows()
        except Exception as exc:
            print(
                f"[WINDOW] Could not enumerate windows: {exc}",
                flush=True,
            )
            return False

        for window in windows:
            try:
                title = (window.window_text() or "").strip()
                class_name = (window.class_name() or "").strip()

                if (
                    title == WHATSAPP_TITLE
                    and class_name == WHATSAPP_CLASS
                ):
                    self.window = window
                    print("[WINDOW] WhatsApp found", flush=True)
                    return True

            except Exception:
                continue

        # Fallback: title-only search. This helps if the class changes.
        for window in windows:
            try:
                title = (window.window_text() or "").strip()

                if title.casefold() == WHATSAPP_TITLE.casefold():
                    self.window = window
                    print(
                        "[WINDOW] WhatsApp found by title fallback",
                        flush=True,
                    )
                    return True

            except Exception:
                continue

        self.window = None
        return False

    # --------------------------------------------------------
    # REQUIRE CONNECTION
    # --------------------------------------------------------

    def require_connection(self):
        if self.window is None:
            if not self.connect():
                raise RuntimeError(
                    "WhatsApp Desktop was not found."
                )

    # --------------------------------------------------------
    # FORCE FOREGROUND
    # --------------------------------------------------------

    @staticmethod
    def _force_foreground(window) -> bool:
        try:
            hwnd = window.handle

            ctypes.windll.user32.ShowWindow(hwnd, 9)
            ctypes.windll.user32.SetForegroundWindow(hwnd)

            time.sleep(0.3)
            return True

        except Exception:
            return False

    # --------------------------------------------------------
    # INITIAL ACTIVATE
    #
    # This is the ONLY place that restores/maximizes.
    # --------------------------------------------------------

    def activate(self):
        self.require_connection()

        print("[WINDOW] Preparing WhatsApp...", flush=True)

        try:
            self.window.restore()
        except Exception:
            pass

        time.sleep(0.25)

        try:
            self.window.maximize()
            print("[WINDOW] Maximized", flush=True)
        except Exception as exc:
            print(
                f"[WINDOW] Maximize warning: {exc}",
                flush=True,
            )

        time.sleep(0.5)
        self.focus_only()
        time.sleep(0.3)

    # --------------------------------------------------------
    # FOCUS ONLY
    # --------------------------------------------------------

    def focus_only(self) -> bool:
        self.require_connection()

        print("[WINDOW] Focusing WhatsApp...", flush=True)

        try:
            self.window.set_focus()
            time.sleep(0.25)

            print("[WINDOW] WhatsApp focused", flush=True)
            return True

        except Exception:
            pass

        if self._force_foreground(self.window):
            print("[WINDOW] WhatsApp focused", flush=True)
            return True

        print("[WINDOW] Could not focus WhatsApp", flush=True)
        return False

    # --------------------------------------------------------
    # FOCUS VS CODE
    # --------------------------------------------------------

    def focus_vscode(self) -> bool:
        print(
            "[WINDOW] Returning focus to VS Code...",
            flush=True,
        )

        try:
            windows = self.desktop.windows()
        except Exception:
            return False

        candidates = []

        for window in windows:
            try:
                title = (window.window_text() or "").strip()
                class_name = (window.class_name() or "").strip()

                if (
                    class_name == VSCODE_CLASS
                    and "Visual Studio Code" in title
                ):
                    candidates.append(window)

            except Exception:
                continue

        if not candidates:
            print("[WINDOW] VS Code not found", flush=True)
            return False

        vscode = candidates[0]

        try:
            vscode.restore()
        except Exception:
            pass

        time.sleep(0.2)

        try:
            vscode.set_focus()
            time.sleep(0.2)

            print("[WINDOW] VS Code focused", flush=True)
            return True

        except Exception:
            pass

        if self._force_foreground(vscode):
            print("[WINDOW] VS Code focused", flush=True)
            return True

        print("[WINDOW] Could not focus VS Code", flush=True)
        return False

    # --------------------------------------------------------
    # ROOT
    # --------------------------------------------------------

    def root(self):
        self.require_connection()
        return self.window


# ============================================================
# WHATSAPP UI
# ============================================================

class WhatsAppUI:

    def __init__(self, connection: WhatsAppConnection):
        self.connection = connection

    # --------------------------------------------------------
    # SEARCH BOX
    # --------------------------------------------------------

    def find_search_box(self):

        root = self.connection.root()

        try:
            edits = root.descendants(control_type="Edit")
        except Exception as exc:
            raise RuntimeError(
                f"Unable to inspect Edit controls: {exc}"
            )

        # First: known automation ID
        for edit in edits:
            try:
                if not edit.is_visible():
                    continue

                automation_id = (
                    edit.element_info.automation_id or ""
                )

                if automation_id == SEARCH_AUTOMATION_ID:
                    return edit

            except Exception:
                continue

        # Fallback: left-side search Edit
        for edit in edits:
            try:
                if not edit.is_visible():
                    continue

                rect = edit.rectangle()

                if rect is None:
                    continue

                if rect.left > 450:
                    continue

                if rect.top < 70:
                    continue

                if rect.top > 180:
                    continue

                return edit

            except Exception:
                continue

        return None

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    def search(self, text: str):

        search = self.find_search_box()

        if search is None:
            raise RuntimeError(
                "WhatsApp search box could not be found."
            )

        print("[SEARCH] Search box found", flush=True)

        try:
            search.click_input()
        except Exception as exc:
            raise RuntimeError(
                f"Could not focus search box: {exc}"
            )

        send_keys("^a")
        send_keys("{BACKSPACE}")
        time.sleep(0.2)

        pyperclip.copy(text)
        send_keys("^v")

        print(
            f"[SEARCH] Searching: {text}",
            flush=True,
        )

        time.sleep(1.0)

    # --------------------------------------------------------
    # ATTACHMENT BUTTON
    # --------------------------------------------------------

    def find_attachment_button(self):

        root = self.connection.root()

        try:
            buttons = root.descendants(control_type="Button")
        except Exception:
            return None

        for button in buttons:
            try:
                if not button.is_visible():
                    continue

                name = (
                    button.element_info.name or ""
                ).strip().casefold()

                rect = button.rectangle()

                if rect is None:
                    continue

                if rect.left < RIGHT_PANEL_MIN_LEFT:
                    continue

                if "attach" in name:
                    return button

            except Exception:
                continue

        return None

    # --------------------------------------------------------
    # SECTION HEADERS
    # --------------------------------------------------------

    def _get_section_headers(self):

        root = self.connection.root()

        try:
            texts = root.descendants(control_type="Text")
        except Exception:
            return []

        headers = []

        for text in texts:
            try:
                if not text.is_visible():
                    continue

                name = (
                    text.element_info.name or ""
                ).strip()

                if name not in {
                    "Chats",
                    "Contacts",
                    "Groups in common",
                }:
                    continue

                rect = text.rectangle()

                if rect is None:
                    continue

                if rect.left > 450:
                    continue

                headers.append(
                    {
                        "name": name,
                        "rect": rect,
                    }
                )

            except Exception:
                continue

        headers.sort(
            key=lambda x: (
                x["rect"].top,
                x["rect"].left,
            )
        )

        return headers

    # --------------------------------------------------------
    # EXTRACT NAME
    # --------------------------------------------------------

    def _extract_name(self, item) -> Optional[str]:

        try:
            raw = (
                item.element_info.name or ""
            ).strip()
        except Exception:
            return None

        if not raw:
            return None

        # Example:
        # Amma 9:11 am testing
        # -> Amma
        match = re.search(
            r"\s+\d{1,2}:\d{2}\s*(?:am|pm)\b",
            raw,
            flags=re.IGNORECASE,
        )

        if match:
            name = raw[:match.start()].strip()

            if name:
                return name

        # Example:
        # Amma Yesterday
        # -> Amma
        match = re.search(
            r"\s+(?:Today|Yesterday|"
            r"Monday|Tuesday|Wednesday|"
            r"Thursday|Friday|Saturday|Sunday)\b",
            raw,
            flags=re.IGNORECASE,
        )

        if match:
            name = raw[:match.start()].strip()

            if name:
                return name

        first_line = raw.splitlines()[0].strip()
        return first_line or None

    # --------------------------------------------------------
    # MATCH SCORE
    # --------------------------------------------------------

    @staticmethod
    def _match_score(query: str, candidate: str) -> float:

        query = query.strip().casefold()
        candidate = candidate.strip().casefold()

        if not query or not candidate:
            return 0.0

        if query == candidate:
            return 1.0

        if candidate.startswith(query):
            return 0.95

        tokens = re.findall(r"[\w]+", candidate)

        best = 0.0

        for token in tokens:

            if token == query:
                best = max(best, 0.98)

            elif token.startswith(query):
                best = max(best, 0.90)

            best = max(
                best,
                SequenceMatcher(
                    None,
                    query,
                    token,
                ).ratio(),
            )

        best = max(
            best,
            SequenceMatcher(
                None,
                query,
                candidate,
            ).ratio(),
        )

        return best

    # --------------------------------------------------------
    # GET SEARCH RESULTS
    # --------------------------------------------------------

    def get_chat_results(
        self,
        requested: str,
    ) -> list[ChatResult]:

        root = self.connection.root()
        headers = self._get_section_headers()

        chats_header = None
        contacts_header = None
        groups_header = None

        for header in headers:

            if header["name"] == "Chats":
                chats_header = header

            elif header["name"] == "Contacts":
                contacts_header = header

            elif header["name"] == "Groups in common":
                groups_header = header

        search_top = None

        if chats_header:
            search_top = chats_header["rect"].bottom

        search_bottom = None

        if groups_header:
            search_bottom = groups_header["rect"].top

        try:
            items = root.descendants(control_type="DataItem")
        except Exception as exc:
            raise RuntimeError(
                f"Unable to inspect search results: {exc}"
            )

        requested_cf = requested.strip().casefold()

        results = []
        seen_names = set()

        for item in items:

            try:

                if not item.is_visible():
                    continue

                rect = item.rectangle()

                if rect is None:
                    continue

                if rect.left > 450:
                    continue

                if rect.width() < 100:
                    continue

                if rect.height() < 25:
                    continue

                if search_top is not None:
                    if rect.top <= search_top:
                        continue

                if search_bottom is not None:
                    if rect.bottom >= search_bottom:
                        continue

                chat_name = self._extract_name(item)

                if not chat_name:
                    continue

                chat_name_cf = chat_name.strip().casefold()

                score = self._match_score(
                    requested_cf,
                    chat_name_cf,
                )

                if score < 0.45:
                    continue

                if chat_name_cf in seen_names:
                    continue

                seen_names.add(chat_name_cf)

                raw_name = (
                    item.element_info.name or ""
                ).strip()

                section = "Chats"

                if contacts_header:
                    if rect.top > contacts_header["rect"].bottom:
                        section = "Contacts"

                results.append(
                    ChatResult(
                        name=chat_name,
                        raw_name=raw_name,
                        element=item,
                        rect=rect,
                        section=section,
                    )
                )

            except Exception:
                continue

        results.sort(
            key=lambda result: (
                -self._match_score(
                    requested_cf,
                    result.name,
                ),
                result.rect.top,
                result.rect.left,
            )
        )

        return results

    # --------------------------------------------------------
    # PHONE NUMBER CHECK
    # --------------------------------------------------------

    @staticmethod
    def _looks_like_phone(text: str) -> bool:

        value = text.strip()

        digits = re.sub(
            r"\D",
            "",
            value,
        )

        if len(digits) < 8:
            return False

        remaining = re.sub(
            r"[\d\s()+\-]",
            "",
            value,
        )

        return remaining == ""

    # --------------------------------------------------------
    # VERIFY CURRENT CHAT
    # --------------------------------------------------------

    def verify_current_chat(
        self,
        expected_name: str,
    ) -> bool:

        expected_cf = (
            expected_name.strip().casefold()
        )

        root = self.connection.root()

        # Method 1: composer
        try:
            edits = root.descendants(
                control_type="Edit"
            )
        except Exception:
            edits = []

        prefix = "Type a message to "

        for edit in edits:
            try:

                if not edit.is_visible():
                    continue

                name = (
                    edit.element_info.name or ""
                ).strip()

                if not name:
                    continue

                if not name.startswith(prefix):
                    continue

                current = (
                    name[len(prefix):].strip()
                )

                if current.casefold() == expected_cf:

                    print(
                        f"[VERIFY] Composer confirms: {current}",
                        flush=True,
                    )

                    return True

            except Exception:
                continue

        # Method 2: other accessible controls
        control_types = [
            "Text",
            "Button",
            "DataItem",
            "Custom",
            "Group",
        ]

        for control_type in control_types:

            try:
                controls = root.descendants(
                    control_type=control_type
                )
            except Exception:
                continue

            for control in controls:

                try:

                    if not control.is_visible():
                        continue

                    name = (
                        control.element_info.name or ""
                    ).strip()

                    if not name:
                        continue

                    if self._looks_like_phone(name):
                        continue

                    normalized = re.sub(
                        r"\s+",
                        " ",
                        name,
                    ).strip().casefold()

                    if normalized != expected_cf:
                        continue

                    rect = control.rectangle()

                    if rect is None:
                        continue

                    if rect.left < RIGHT_PANEL_MIN_LEFT:
                        continue

                    print(
                        f"[VERIFY] Accessible control confirms: '{name}'",
                        flush=True,
                    )

                    return True

                except Exception:
                    continue

        return False

    # --------------------------------------------------------
    # OPEN ATTACHMENT MENU
    # --------------------------------------------------------

    def open_attachment_menu(self):

        button = self.find_attachment_button()

        if button is None:
            raise RuntimeError(
                "Attachment button was not found."
            )

        print(
            "[ATTACHMENT] Clicking attachment button...",
            flush=True,
        )

        button.click_input()
        time.sleep(0.5)

    # --------------------------------------------------------
    # FIND ATTACHMENT MENU ITEM
    # --------------------------------------------------------

    def find_attachment_menu_item(
        self,
        item_name: str,
    ):

        root = self.connection.root()

        target = item_name.strip().casefold()

        print(
            f"[ATTACHMENT] Looking for menu item: {item_name}",
            flush=True,
        )

        try:
            controls = root.descendants()
        except Exception as exc:
            print(
                f"[ATTACHMENT] Could not read UI: {exc}",
                flush=True,
            )
            return None

        # Exact match
        for control in controls:

            try:

                if not control.is_visible():
                    continue

                name = (
                    control.element_info.name or ""
                ).strip()

                if name.casefold() == target:
                    return control

            except Exception:
                continue

        # Partial match
        for control in controls:

            try:

                if not control.is_visible():
                    continue

                name = (
                    control.element_info.name or ""
                ).strip()

                if target in name.casefold():
                    return control

            except Exception:
                continue

        return None

    # --------------------------------------------------------
    # CHOOSE ATTACHMENT TYPE
    # --------------------------------------------------------

    def choose_attachment_type(
        self,
        attachment_type: str,
    ):

        control = self.find_attachment_menu_item(
            attachment_type
        )

        if control is None:
            raise RuntimeError(
                f"Attachment menu item "
                f"'{attachment_type}' was not found."
            )

        try:
            control_type = (
                control.element_info.control_type
            )
        except Exception:
            control_type = "Unknown"

        try:
            rect = control.rectangle()
        except Exception:
            rect = None

        print(
            f"[ATTACHMENT] Found: '{attachment_type}'",
            flush=True,
        )

        print(
            f"[ATTACHMENT] Control type: {control_type}",
            flush=True,
        )

        print(
            f"[ATTACHMENT] Rectangle: {rect}",
            flush=True,
        )

        print(
            f"[ATTACHMENT] Clicking '{attachment_type}'...",
            flush=True,
        )

        control.click_input()
        time.sleep(1.0)

        print(
            f"[ATTACHMENT] '{attachment_type}' selected",
            flush=True,
        )

    # --------------------------------------------------------
    # FIND COMPOSER
    # --------------------------------------------------------

    def find_composer(self):

        root = self.connection.root()

        try:
            edits = root.descendants(
                control_type="Edit"
            )
        except Exception:
            return None

        for edit in edits:

            try:

                if not edit.is_visible():
                    continue

                rect = edit.rectangle()

                if rect is None:
                    continue

                if rect.left < RIGHT_PANEL_MIN_LEFT:
                    continue

                name = (
                    edit.element_info.name or ""
                ).strip()

                if "Type a message" in name:
                    return edit

            except Exception:
                continue

        return None


# ============================================================
# MESSAGE AUTOMATION
# ============================================================

class WhatsAppMessage:

    def __init__(
        self,
        connection: WhatsAppConnection,
        ui: WhatsAppUI,
    ):
        self.connection = connection
        self.ui = ui

    # --------------------------------------------------------
    # OCR: CAPTURE CHAT MESSAGE AREA
    # --------------------------------------------------------

    def _capture_chat_area(self, save_path: Optional[Union[str, Path]] = None):
        """
        Capture only the WhatsApp message area.

        The left chat list, top chat header, and bottom composer are
        deliberately excluded so Tesseract sees mostly message content.
        """
        self.connection.focus_only()
        time.sleep(0.25)

        root = self.connection.root()
        rect = root.rectangle()
        if rect is None:
            raise RuntimeError("Could not get WhatsApp window rectangle.")

        window_left = rect.left
        window_top = rect.top
        window_width = rect.right - rect.left
        window_height = rect.bottom - rect.top

        if window_width <= 0 or window_height <= 0:
            raise RuntimeError("Invalid WhatsApp window rectangle.")

        # Right-side chat starts after the left chat list.
        left = window_left + RIGHT_PANEL_MIN_LEFT
        right = rect.right

        # Exclude WhatsApp title/header and the message composer.
        top = window_top + 105
        bottom = rect.bottom - 105

        if right <= left or bottom <= top:
            raise RuntimeError("Invalid WhatsApp chat capture region.")

        region = (
            int(left),
            int(top),
            int(right),
            int(bottom),
        )

        print(
            f"[OCR] Capture region: L={region[0]}, T={region[1]}, "
            f"R={region[2]}, B={region[3]}",
            flush=True,
        )

        image = pyautogui.screenshot(region=(
            region[0],
            region[1],
            region[2] - region[0],
            region[3] - region[1],
        ))

        if save_path is None:
            save_path = OCR_SCREENSHOT_PATH

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(save_path)

        print(
            f"[SCREENSHOT] Saved: {save_path}",
            flush=True,
        )

        return image

    # --------------------------------------------------------
    # OCR: PREPROCESS
    # --------------------------------------------------------

    @staticmethod
    def _preprocess_for_ocr(image):
        """
        Prepare WhatsApp's dark UI for Tesseract.

        Grayscale + contrast + light sharpening improves text detection
        without changing the original screenshot saved for debugging.
        """
        gray = ImageOps.grayscale(image)
        gray = ImageOps.autocontrast(gray)
        gray = gray.resize(
            (gray.width * 2, gray.height * 2)
        )
        gray = gray.filter(ImageFilter.SHARPEN)
        return gray

    # --------------------------------------------------------
    # OCR: CLEAN TEXT
    # --------------------------------------------------------

    @staticmethod
    def _clean_ocr_text(text: str) -> str:
        """Normalize common OCR whitespace/noise while preserving messages."""
        lines = []

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            # Remove repeated whitespace but keep normal sentence spacing.
            line = re.sub(r"[ \t]+", " ", line)

            # Common WhatsApp/Tesseract artefacts.
            line = line.replace("© Forwarded", "Forwarded")
            line = line.replace("©Forwarded", "Forwarded")
            line = re.sub(r"^[-•·]+$", "", line).strip()

            if line:
                lines.append(line)

        return "\n".join(lines)

    # --------------------------------------------------------
    # READ MESSAGES FROM CURRENT CHAT
    # --------------------------------------------------------

    def read_current_chat_messages(
        self,
        save_screenshot: bool = True,
    ) -> dict:
        """
        Read visible messages from the currently opened WhatsApp chat
        using Tesseract OCR.

        This reads what is currently visible on screen. It does not scroll
        through older messages and it does not modify/send anything.
        """
        self.connection.focus_only()
        time.sleep(0.25)

        print("[OCR] Checking Tesseract...", flush=True)
        try:
            version = str(pytesseract.get_tesseract_version())
            print(
                f"[OCR] Tesseract: {version.splitlines()[0]}",
                flush=True,
            )
        except Exception as exc:
            raise RuntimeError(
                "Tesseract could not be started. "
                "Install Tesseract or set TESSERACT_DEFAULT_PATH. "
                f"Details: {exc}"
            )

        print("[SCREENSHOT] Capturing WhatsApp chat area...", flush=True)

        save_path = OCR_SCREENSHOT_PATH if save_screenshot else None
        image = self._capture_chat_area(save_path)

        print("[OCR] Preprocessing screenshot...", flush=True)
        processed = self._preprocess_for_ocr(image)

        print("[OCR] Running OCR...", flush=True)
        started = time.perf_counter()

        # psm 6 works well for a block of WhatsApp message text.
        raw_text = pytesseract.image_to_string(
            processed,
            lang="eng",
            config="--oem 3 --psm 6",
        )

        elapsed = time.perf_counter() - started
        cleaned = self._clean_ocr_text(raw_text)
        message_lines = [
            line for line in cleaned.splitlines()
            if line.strip()
        ]

        print(
            f"[OCR] Completed in {elapsed:.2f} seconds",
            flush=True,
        )

        return {
            "success": True,
            "text": cleaned,
            "lines": message_lines,
            "raw_text": raw_text,
            "ocr_seconds": round(elapsed, 3),
            "screenshot": str(OCR_SCREENSHOT_PATH) if save_screenshot else None,
            "count": len(message_lines),
        }

    # --------------------------------------------------------
    # READ MESSAGES FROM A SPECIFIC CHAT
    # --------------------------------------------------------

    def read_messages(
        self,
        contact: str,
        save_screenshot: bool = True,
    ) -> dict:
        """
        Open/verify a specific WhatsApp chat and OCR the visible messages.
        """
        if not contact.strip():
            raise ValueError("Contact cannot be empty.")

        selected_chat = self.resolve_and_select_chat(contact)

        print(
            f"[CHAT] Verified chat: {selected_chat}",
            flush=True,
        )
        print("[MESSAGE] Reading visible messages...", flush=True)

        result = self.read_current_chat_messages(
            save_screenshot=save_screenshot,
        )

        result["chat"] = selected_chat
        return result

    # --------------------------------------------------------
    # ASK USER TO CHOOSE
    # --------------------------------------------------------

    def ask_user_to_choose(
        self,
        requested: str,
        matches: list[ChatResult],
    ) -> Optional[ChatResult]:

        self.connection.focus_vscode()

        print()
        print("=" * 60)
        print(
            f"Multiple chats/contacts match '{requested}'"
        )
        print("=" * 60)

        for index, result in enumerate(
            matches,
            start=1,
        ):
            print(
                f"{index}. "
                f"{result.name} "
                f"[{result.section}]"
            )

        print()
        print("Choose the chat/contact.")

        while True:

            answer = input(
                "Choice (or q to cancel): "
            ).strip()

            if answer.casefold() == "q":
                return None

            try:
                choice = int(answer)
            except ValueError:
                print("Please enter a number.")
                continue

            if 1 <= choice <= len(matches):

                selected = matches[choice - 1]

                print(
                    f"[CHAT] You selected: {selected.name}"
                )

                return selected

            print("Invalid choice.")

    # --------------------------------------------------------
    # WINDOWS OPEN FILE DIALOG
    #
    # This is used for EVERY file:
    #
    #     Windows Open dialog
    #     -> File name
    #     -> Open
    #
    # --------------------------------------------------------

    def _select_file_from_open_dialog(
        self,
        file_path: str,
    ):

        print(
            "[FILE] Waiting for Windows Open dialog...",
            flush=True,
        )

        dialog = None

        deadline = time.time() + TIMEOUT

        while time.time() < deadline:

            try:

                desktop = Desktop(backend="win32")

                for window in desktop.windows():

                    try:

                        if not window.is_visible():
                            continue

                        title = (
                            window.window_text() or ""
                        ).strip()

                        class_name = (
                            window.class_name() or ""
                        ).strip()

                        if (
                            title.casefold() == "open"
                            and class_name == "#32770"
                        ):
                            dialog = window
                            break

                    except Exception:
                        continue

                if dialog is not None:
                    break

            except Exception:
                pass

            time.sleep(POLL_INTERVAL)

        if dialog is None:
            raise RuntimeError(
                "Windows Open dialog was not found."
            )

        print(
            "[FILE] Windows Open dialog found",
            flush=True,
        )

        print(
            f"[FILE] Dialog handle: {dialog.handle}",
            flush=True,
        )

        try:
            dialog.set_focus()
        except Exception:
            pass

        time.sleep(0.2)

        # ----------------------------------------------------
        # Find File name Edit
        # ----------------------------------------------------

        file_edit = None

        try:

            edits = dialog.children(
                class_name="Edit"
            )

            for edit in edits:

                try:

                    if edit.is_visible():
                        file_edit = edit
                        break

                except Exception:
                    continue

        except Exception:
            file_edit = None

        if file_edit is None:
            raise RuntimeError(
                "File name Edit control was not found."
            )

        print(
            "[FILE] File name field found",
            flush=True,
        )

        # ----------------------------------------------------
        # Enter FULL FILE PATH
        # ----------------------------------------------------

        file_edit.click_input()
        time.sleep(0.1)

        pyperclip.copy(file_path)

        send_keys("^a")
        time.sleep(0.1)
        send_keys("^v")

        print(
            f"[FILE] Path entered: {file_path}",
            flush=True,
        )

        time.sleep(0.3)

        # ----------------------------------------------------
        # Find Open button
        # ----------------------------------------------------

        open_button = None

        try:

            open_button = dialog.child_window(
                title="&Open",
                class_name="Button",
            )

            if not open_button.exists(timeout=2):
                open_button = None

        except Exception:
            open_button = None

        # Fallback
        if open_button is None:

            try:

                buttons = dialog.children(
                    class_name="Button"
                )

                for button in buttons:

                    try:

                        if not button.is_visible():
                            continue

                        title = (
                            button.window_text() or ""
                        ).strip()

                        if title.casefold() in {
                            "&open",
                            "open",
                        }:
                            open_button = button
                            break

                    except Exception:
                        continue

            except Exception:
                pass

        if open_button is None:
            raise RuntimeError(
                "Open button was not found."
            )

        print(
            "[FILE] Open button found",
            flush=True,
        )

        print(
            "[FILE] Clicking Open...",
            flush=True,
        )

        open_button.click_input()

        # ----------------------------------------------------
        # Wait for dialog to disappear
        # ----------------------------------------------------

        deadline = time.time() + TIMEOUT

        while time.time() < deadline:

            try:

                if not dialog.exists():
                    break

            except Exception:
                break

            time.sleep(POLL_INTERVAL)

        time.sleep(1.0)

        print(
            "[FILE] File picker closed",
            flush=True,
        )

        print(
            "[FILE] File handed to WhatsApp",
            flush=True,
        )

        # The Windows Open dialog owns the foreground while the file
        # is selected. Explicitly return focus to WhatsApp before the
        # next UIA operation (especially before clicking Add file).
        self.connection.focus_only()
        time.sleep(0.35)

    # --------------------------------------------------------
    # FILE TYPE
    # --------------------------------------------------------

    @staticmethod
    def _attachment_type_for_file(
        file_path: str,
    ) -> str:

        extension = (
            Path(file_path).suffix.lower()
        )

        image_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif",
            ".bmp",
        }

        video_extensions = {
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".webm",
        }

        audio_extensions = {
            ".mp3",
            ".wav",
            ".m4a",
            ".aac",
            ".ogg",
        }

        if extension in image_extensions:
            return "Photos & videos"

        if extension in video_extensions:
            return "Photos & videos"

        if extension in audio_extensions:
            return "Audio"

        return "Document"

    # --------------------------------------------------------
    # FIND + BUTTON
    #
    # Strategy:
    # 1. Accessibility/name/automation id
    # 2. Geometry fallback
    #
    # IMPORTANT:
    # We deliberately exclude the green Send button area.
    # --------------------------------------------------------

    def _find_attachment_plus_button(self):
        """
        Find the '+' / 'Add file' button in WhatsApp's attachment
        preview.

        The UI inspection showed that the current WhatsApp Desktop
        exposes this button as:

            Name        = "Add file"
            ControlType = Button
            Rectangle   = L=1209, T=1048, R=1274, B=1114

        There can be many duplicate UIA entries for the same button,
        so we deduplicate by screen rectangle and prefer the exact
        accessibility name instead of using a generic "add" match.
        """

        print(
            "[ATTACHMENT] Looking for + / Add file button...",
            flush=True,
        )

        # The file picker can steal focus. Always bring WhatsApp back
        # to the foreground before inspecting the UIA tree.
        self.connection.focus_only()
        time.sleep(0.25)

        root = self.connection.root()

        try:
            buttons = root.descendants(control_type="Button")
        except Exception as exc:
            print(
                f"[ATTACHMENT] Could not inspect buttons: {exc}",
                flush=True,
            )
            return None

        try:
            whatsapp_rect = root.rectangle()
        except Exception:
            whatsapp_rect = None

        # --------------------------------------------------------
        # Collect visible unique candidates.
        # --------------------------------------------------------

        exact_candidates = []
        fallback_candidates = []
        seen_rects = set()

        for button in buttons:
            try:
                if not button.is_visible():
                    continue

                rect = button.rectangle()
                if rect is None:
                    continue

                # Deduplicate the repeated UIA entries observed in
                # the inspection. The same Add file button appeared
                # many times with exactly the same rectangle.
                rect_key = (
                    rect.left,
                    rect.top,
                    rect.right,
                    rect.bottom,
                )

                if rect_key in seen_rects:
                    continue

                seen_rects.add(rect_key)

                # The attachment preview is on the right side.
                if rect.left < RIGHT_PANEL_MIN_LEFT:
                    continue

                if rect.width() <= 0 or rect.height() <= 0:
                    continue

                name = (
                    button.element_info.name or ""
                ).strip()

                automation_id = (
                    button.element_info.automation_id or ""
                ).strip()

                help_text = ""
                try:
                    help_text = (
                        button.element_info.help_text or ""
                    ).strip()
                except Exception:
                    pass

                combined = (
                    f"{name} "
                    f"{automation_id} "
                    f"{help_text}"
                ).casefold()

                # ------------------------------------------------
                # BEST MATCH:
                # The inspected WhatsApp UI exposes the button
                # specifically as "Add file".
                # ------------------------------------------------

                if name.casefold() == "add file":
                    exact_candidates.append(
                        (
                            1000,
                            button,
                            name,
                            rect,
                        )
                    )
                    continue

                # Also accept an accessibility/help-text match
                # for future WhatsApp UI changes.
                if any(
                    keyword in combined
                    for keyword in (
                        "add file",
                        "attach file",
                        "add attachment",
                    )
                ):
                    exact_candidates.append(
                        (
                            900,
                            button,
                            name,
                            rect,
                        )
                    )
                    continue

                # ------------------------------------------------
                # GEOMETRY FALLBACK
                # ------------------------------------------------
                #
                # Current inspected UI:
                #   Add file = (1209,1048)-(1274,1114)
                #
                # Send button:
                #   (1825,1041)-(1900,1117)
                #
                # Therefore we deliberately reject the far-right
                # Send area.
                # ------------------------------------------------

                if whatsapp_rect is None:
                    continue

                window_width = (
                    whatsapp_rect.right -
                    whatsapp_rect.left
                )

                window_height = (
                    whatsapp_rect.bottom -
                    whatsapp_rect.top
                )

                if window_width <= 0 or window_height <= 0:
                    continue

                relative_left = (
                    rect.left - whatsapp_rect.left
                )
                relative_top = (
                    rect.top - whatsapp_rect.top
                )

                # Attachment preview controls are near the bottom.
                if relative_top < window_height * 0.75:
                    continue

                # Exclude the far-right Send button.
                if relative_left >= window_width * 0.80:
                    continue

                # The Add file button is a small square button.
                if rect.width() > 100 or rect.height() > 100:
                    continue

                # Prefer a button close to the known inspected
                # location, but do not hard-code the screen
                # coordinates as the only solution.
                fallback_candidates.append(
                    (
                        50,
                        button,
                        name,
                        rect,
                    )
                )

            except Exception:
                continue

        # --------------------------------------------------------
        # Prefer exact accessibility match.
        # --------------------------------------------------------

        candidates = (
            exact_candidates
            if exact_candidates
            else fallback_candidates
        )

        if not candidates:
            print(
                "[ATTACHMENT] Add file / + button not found.",
                flush=True,
            )
            return None

        # Prefer highest score, then the lowest/leftmost matching
        # button. This makes duplicate UIA entries deterministic.
        candidates.sort(
            key=lambda item: (
                -item[0],
                item[3].top,
                item[3].left,
            )
        )

        _, button, name, rect = candidates[0]

        print(
            f"[ATTACHMENT] + button found: '{name}'",
            flush=True,
        )
        print(
            f"[ATTACHMENT] + rectangle: {rect}",
            flush=True,
        )

        return button

    # --------------------------------------------------------
    # CLICK +
    # --------------------------------------------------------

    def _click_attachment_plus(self):
        """
        Click WhatsApp's Add file / '+' button.

        The button is searched fresh every time because the WhatsApp
        attachment preview can rebuild its UIA elements after a file
        is added.
        """

        last_error = None

        for attempt in range(1, 4):
            print(
                f"[ATTACHMENT] Looking for + button "
                f"(attempt {attempt}/3)...",
                flush=True,
            )

            try:
                # Re-focus WhatsApp before every UI inspection.
                self.connection.focus_only()
                time.sleep(0.25)

                button = self._find_attachment_plus_button()

                if button is None:
                    last_error = (
                        "Add file button was not found."
                    )
                    time.sleep(0.5)
                    continue

                print(
                    "[ATTACHMENT] Clicking Add file / +...",
                    flush=True,
                )

                try:
                    button.click_input()
                except Exception:
                    # UIA elements can become stale when the preview
                    # is rebuilt. Re-acquire once immediately.
                    self.connection.focus_only()
                    time.sleep(0.25)

                    button = (
                        self._find_attachment_plus_button()
                    )

                    if button is None:
                        raise

                    button.click_input()

                time.sleep(0.75)

                print(
                    "[ATTACHMENT] Add file / + clicked",
                    flush=True,
                )
                return

            except Exception as exc:
                last_error = exc
                print(
                    f"[ATTACHMENT] + click attempt "
                    f"{attempt} failed: {exc}",
                    flush=True,
                )
                time.sleep(0.5)

        raise RuntimeError(
            "WhatsApp attachment '+' / 'Add file' button "
            f"could not be clicked. Last error: {last_error}"
        )

    # --------------------------------------------------------
    # ADD ONE FILE
    # --------------------------------------------------------

    def _add_file_using_picker(
        self,
        file_path: str,
    ):

        file_path = os.path.abspath(
            os.path.expanduser(
                file_path.strip()
            )
        )

        if not os.path.isfile(file_path):
            raise FileNotFoundError(
                f"File does not exist: {file_path}"
            )

        print(
            f"[FILE] Selecting: {file_path}",
            flush=True,
        )

        self._select_file_from_open_dialog(
            file_path
        )

        print(
            f"[FILE] Selected: {file_path}",
            flush=True,
        )

        # Give WhatsApp time to rebuild the attachment preview and
        # expose the Add file button.
        time.sleep(1.25)

        self.connection.focus_only()
        time.sleep(0.25)

    # --------------------------------------------------------
    # FIND CAPTION BOX
    # --------------------------------------------------------

    def _find_caption_box(self):

        root = self.connection.root()

        try:
            edits = root.descendants(
                control_type="Edit"
            )
        except Exception:
            return None

        candidates = []

        for edit in edits:

            try:

                if not edit.is_visible():
                    continue

                rect = edit.rectangle()

                if rect is None:
                    continue

                if rect.left < RIGHT_PANEL_MIN_LEFT:
                    continue

                name = (
                    edit.element_info.name or ""
                ).strip()

                # Normal message composer is NOT the caption box.
                if "Type a message" in name:
                    continue

                candidates.append(
                    (
                        rect.top,
                        rect.left,
                        edit,
                    )
                )

            except Exception:
                continue

        if not candidates:
            return None

        # Caption box is normally the lowest right-side Edit.
        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        return candidates[0][2]

    # --------------------------------------------------------
    # ENTER CAPTION
    # --------------------------------------------------------

    def _enter_caption(
        self,
        message: str,
    ):

        if not message:
            return

        print(
            "[ATTACHMENT] Adding caption...",
            flush=True,
        )

        caption_box = self._find_caption_box()

        if caption_box is None:
            print(
                "[ATTACHMENT] Caption box not found; "
                "continuing without caption.",
                flush=True,
            )
            return

        try:

            caption_box.click_input()

            pyperclip.copy(message)
            send_keys("^v")

            print(
                "[ATTACHMENT] Caption entered",
                flush=True,
            )

        except Exception as exc:

            print(
                f"[ATTACHMENT] Could not enter caption: {exc}",
                flush=True,
            )

    # --------------------------------------------------------
    # CLICK WHATSAPP ATTACHMENT SEND BUTTON
    # --------------------------------------------------------

    def _click_attachment_send(self) -> bool:

        print(
            "[ATTACHMENT] Looking for WhatsApp Send button...",
            flush=True,
        )

        time.sleep(1.5)

        # ====================================================
        # METHOD 1: UIA
        # ====================================================

        try:

            print(
                "[SEND] Searching UIA buttons...",
                flush=True,
            )

            desktop = Desktop(backend="uia")

            whatsapp = desktop.window(
                title_re=".*WhatsApp.*"
            )

            if whatsapp.exists(timeout=2):

                try:
                    buttons = whatsapp.descendants(
                        control_type="Button"
                    )
                except Exception:
                    buttons = []

                try:
                    whatsapp_rect = whatsapp.rectangle()
                except Exception:
                    whatsapp_rect = None

                for button in buttons:

                    try:

                        if not button.is_visible():
                            continue

                        rect = button.rectangle()

                        if rect is None:
                            continue

                        if whatsapp_rect is not None:

                            width = (
                                whatsapp_rect.right
                                - whatsapp_rect.left
                            )

                            height = (
                                whatsapp_rect.bottom
                                - whatsapp_rect.top
                            )

                            relative_left = (
                                rect.left
                                - whatsapp_rect.left
                            )

                            relative_top = (
                                rect.top
                                - whatsapp_rect.top
                            )

                            if relative_left < (
                                width * 0.70
                            ):
                                continue

                            if relative_top < (
                                height * 0.65
                            ):
                                continue

                        name = (
                            button.element_info.name or ""
                        ).strip()

                        automation_id = (
                            button.element_info.automation_id or ""
                        ).strip()

                        help_text = ""

                        try:
                            help_text = (
                                button.element_info.help_text or ""
                            ).strip()
                        except Exception:
                            pass

                        combined = (
                            f"{name} "
                            f"{automation_id} "
                            f"{help_text}"
                        ).casefold()

                        if "send" not in combined:
                            continue

                        print(
                            f"[SEND] Found UIA Send button: '{name}'",
                            flush=True,
                        )

                        print(
                            f"[SEND] Rectangle: {rect}",
                            flush=True,
                        )

                        button.click_input()

                        print(
                            "[SEND] UIA Send clicked",
                            flush=True,
                        )

                        time.sleep(1.5)
                        return True

                    except Exception:
                        continue

        except Exception as exc:

            print(
                f"[SEND] UIA search failed: {exc}",
                flush=True,
            )

        # ====================================================
        # METHOD 2: WIN32
        # ====================================================

        try:

            print(
                "[SEND] Searching Win32 buttons...",
                flush=True,
            )

            desktop = Desktop(backend="win32")
            whatsapp = None

            for window in desktop.windows():

                try:

                    title = (
                        window.window_text() or ""
                    ).strip()

                    if title.casefold() == "whatsapp":
                        whatsapp = window
                        break

                except Exception:
                    continue

            if whatsapp is not None:

                try:
                    buttons = whatsapp.children(
                        class_name="Button"
                    )
                except Exception:
                    buttons = []

                for button in buttons:

                    try:

                        if not button.is_visible():
                            continue

                        title = (
                            button.window_text() or ""
                        ).strip()

                        if "send" not in title.casefold():
                            continue

                        rect = button.rectangle()

                        print(
                            f"[SEND] Found Win32 Send: '{title}'",
                            flush=True,
                        )

                        print(
                            f"[SEND] Rectangle: {rect}",
                            flush=True,
                        )

                        button.click_input()

                        print(
                            "[SEND] Win32 Send clicked",
                            flush=True,
                        )

                        time.sleep(1.5)
                        return True

                    except Exception:
                        continue

        except Exception as exc:

            print(
                f"[SEND] Win32 search failed: {exc}",
                flush=True,
            )

        # ====================================================
        # METHOD 3: POSITION FALLBACK
        #
        # Based on the current UI shown in your screenshot.
        # Uses actual WhatsApp window rectangle, not screen size.
        # ====================================================

        try:

            print(
                "[SEND] UI element not exposed.",
                flush=True,
            )

            print(
                "[SEND] Using maximized-window position fallback...",
                flush=True,
            )

            import win32gui
            import pyautogui

            hwnd = None

            def enum_windows_callback(handle, _):

                nonlocal hwnd

                try:

                    if not win32gui.IsWindowVisible(handle):
                        return

                    title = (
                        win32gui.GetWindowText(handle) or ""
                    ).strip()

                    if title.casefold() == "whatsapp":
                        hwnd = handle

                except Exception:
                    pass

            win32gui.EnumWindows(
                enum_windows_callback,
                None,
            )

            if hwnd is None:
                raise RuntimeError(
                    "WhatsApp window handle not found."
                )

            win32gui.ShowWindow(hwnd, 3)
            win32gui.SetForegroundWindow(hwnd)

            time.sleep(0.5)

            left, top, right, bottom = (
                win32gui.GetWindowRect(hwnd)
            )

            print(
                "[SEND] WhatsApp window:",
                f"L={left}",
                f"T={top}",
                f"R={right}",
                f"B={bottom}",
                flush=True,
            )

            # Your current screenshot:
            # Send button is approximately this far from
            # the lower-right window corner.
            send_x = right - 44
            send_y = bottom - 52

            print(
                f"[SEND] Clicking fallback position: "
                f"({send_x}, {send_y})",
                flush=True,
            )

            pyautogui.click(
                send_x,
                send_y,
            )

            print(
                "[SEND] Fallback Send clicked",
                flush=True,
            )

            time.sleep(1.5)
            return True

        except Exception as exc:

            print(
                f"[SEND] Position fallback failed: {exc}",
                flush=True,
            )

            return False

    # --------------------------------------------------------
    # ASK FOR ANOTHER CHAT NAME
    # --------------------------------------------------------

    def ask_for_chat_name(
        self,
        requested: str,
    ) -> Optional[str]:

        self.connection.focus_vscode()

        print()
        print("=" * 60)
        print(
            f"No chat/contact found for '{requested}'"
        )
        print("=" * 60)

        print(
            "Enter another name or q to cancel."
        )

        while True:

            answer = input(
                "Chat/contact name: "
            ).strip()

            if answer.casefold() == "q":
                return None

            if answer:
                return answer

            print("Name cannot be empty.")

    # --------------------------------------------------------
    # RESOLVE CHAT
    # --------------------------------------------------------

    def resolve_and_select_chat(
        self,
        requested: str,
    ) -> str:

        requested = requested.strip()

        if not requested:
            raise ValueError(
                "Chat/contact name cannot be empty."
            )

        # Initial WhatsApp preparation
        self.connection.activate()

        while True:

            self.ui.search(requested)

            results = self.ui.get_chat_results(
                requested
            )

            print(
                f"[SEARCH] Search results found: {len(results)}",
                flush=True,
            )

            for result in results:

                print(
                    f"        - "
                    f"{result.name} "
                    f"[{result.section}]",
                    flush=True,
                )

            # ------------------------------------------------
            # ZERO RESULTS
            # ------------------------------------------------

            if not results:

                new_name = self.ask_for_chat_name(
                    requested
                )

                if new_name is None:
                    raise UserCancelled(
                        "User cancelled."
                    )

                requested = new_name
                self.connection.focus_only()
                continue

            # ------------------------------------------------
            # EXACT MATCH
            # ------------------------------------------------

            exact = [
                result
                for result in results
                if (
                    result.name.casefold()
                    == requested.casefold()
                )
            ]

            if len(exact) == 1:

                selected = exact[0]

                print(
                    f"[CHAT] Exact match: {selected.name}",
                    flush=True,
                )

            # ------------------------------------------------
            # MULTIPLE EXACT MATCHES
            # ------------------------------------------------

            elif len(exact) > 1:

                selected = self.ask_user_to_choose(
                    requested,
                    exact,
                )

                if selected is None:
                    raise UserCancelled(
                        "User cancelled."
                    )

                self.connection.focus_only()

            # ------------------------------------------------
            # SIMILAR MATCHES
            # ------------------------------------------------

            elif len(results) > 1:

                selected = self.ask_user_to_choose(
                    requested,
                    results,
                )

                if selected is None:
                    raise UserCancelled(
                        "User cancelled."
                    )

                self.connection.focus_only()

            # ------------------------------------------------
            # ONE NON-EXACT RESULT
            # ------------------------------------------------

            else:

                selected = results[0]

                print(
                    f"[CHAT] Unique match: {selected.name}",
                    flush=True,
                )

            # ------------------------------------------------
            # CLICK SELECTED RESULT
            # ------------------------------------------------

            if selected.element is None:
                raise RuntimeError(
                    "Selected result has no UI element."
                )

            print(
                f"[CHAT] Clicking: {selected.name}",
                flush=True,
            )

            try:
                selected.element.click_input()
            except Exception as exc:
                raise RuntimeError(
                    f"Could not click "
                    f"'{selected.name}': {exc}"
                )

            time.sleep(0.6)

            # ------------------------------------------------
            # VERIFY OPENED CHAT
            # ------------------------------------------------

            print(
                "[CHAT] Verifying opened chat...",
                flush=True,
            )

            deadline = time.time() + TIMEOUT

            while time.time() < deadline:

                if self.ui.verify_current_chat(
                    selected.name
                ):

                    print(
                        f"[CHAT] Verified: {selected.name}",
                        flush=True,
                    )

                    return selected.name

                time.sleep(POLL_INTERVAL)

            raise ChatVerificationFailed(
                f"Selected chat '{selected.name}', "
                f"but WhatsApp did not verify "
                f"the same chat."
            )

    # --------------------------------------------------------
    # SEND MESSAGE
    # --------------------------------------------------------

    def send(
        self,
        contact: str,
        message: str,
    ):

        if not contact.strip():
            raise ValueError(
                "Contact cannot be empty."
            )

        if not message:
            raise ValueError(
                "Message cannot be empty."
            )

        selected_chat = (
            self.resolve_and_select_chat(
                contact
            )
        )

        print(
            "[MESSAGE] Finding composer...",
            flush=True,
        )

        composer = self.ui.find_composer()

        if composer is None:
            raise RuntimeError(
                "Message composer was not found."
            )

        print(
            f"[CHAT] Verified chat: {selected_chat}",
            flush=True,
        )

        try:
            composer.click_input()
        except Exception as exc:
            raise RuntimeError(
                f"Could not focus message composer: {exc}"
            )

        pyperclip.copy(message)
        send_keys("^v")

        print(
            "[MESSAGE] Message entered",
            flush=True,
        )

        time.sleep(0.2)

        send_keys("{ENTER}")

        print(
            "[MESSAGE] Message sent",
            flush=True,
        )

        time.sleep(0.5)

        return {
            "success": True,
            "chat": selected_chat,
            "message": message,
        }

    # --------------------------------------------------------
    # NORMALIZE MULTIPLE FILE PATHS
    # --------------------------------------------------------

    @staticmethod
    def _normalize_file_paths(
        file_path: Union[str, Path, list[str], tuple[str, ...]],
    ) -> list[str]:

        if isinstance(file_path, (str, Path)):

            paths = [str(file_path)]

        elif isinstance(file_path, (list, tuple)):

            paths = [str(path) for path in file_path]

        else:

            raise TypeError(
                "file_path must be a string, Path, "
                "list, or tuple."
            )

        normalized = []

        for path in paths:

            path = path.strip()

            if not path:
                continue

            path = os.path.abspath(
                os.path.expanduser(path)
            )

            if not os.path.isfile(path):
                raise FileNotFoundError(
                    f"File does not exist: {path}"
                )

            normalized.append(path)

        if not normalized:
            raise ValueError(
                "At least one valid file is required."
            )

        return normalized

    # --------------------------------------------------------
    # SEND ATTACHMENT(S)
    #
    # SINGLE FILE:
    #
    #     attachment -> Document/Photos/Audio
    #     -> Windows Open -> file
    #     -> caption -> Send
    #
    # MULTIPLE FILES:
    #
    #     first file:
    #         attachment -> type -> Windows Open -> file
    #
    #     every additional file:
    #         + -> Windows Open -> file
    #
    #     finally:
    #         caption -> Send
    #
    # --------------------------------------------------------

    def send_attachment(
        self,
        contact: str,
        message: str,
        file_path: Union[
            str,
            Path,
            list[str],
            tuple[str, ...],
        ],
    ):

        file_paths = self._normalize_file_paths(
            file_path
        )

        print()
        print(
            f"[ATTACHMENT] Number of files: "
            f"{len(file_paths)}",
            flush=True,
        )

        for index, path in enumerate(
            file_paths,
            start=1,
        ):
            print(
                f"[ATTACHMENT] "
                f"{index}. {path}",
                flush=True,
            )

        # ----------------------------------------------------
        # RESOLVE + VERIFY CONTACT
        # ----------------------------------------------------

        selected_chat = (
            self.resolve_and_select_chat(
                contact
            )
        )

        print(
            f"[CHAT] Verified chat: {selected_chat}",
            flush=True,
        )

        # ----------------------------------------------------
        # FIRST FILE DETERMINES THE ORIGINAL
        # ATTACHMENT MENU TYPE.
        #
        # Additional files use the + button.
        # ----------------------------------------------------

        first_file = file_paths[0]

        attachment_type = (
            self._attachment_type_for_file(
                first_file
            )
        )

        print(
            f"[ATTACHMENT] First file: {first_file}",
            flush=True,
        )

        print(
            f"[ATTACHMENT] First file type: "
            f"{attachment_type}",
            flush=True,
        )

        # ----------------------------------------------------
        # OPEN ATTACHMENT MENU
        # ----------------------------------------------------

        self.connection.focus_only()

        self.ui.open_attachment_menu()

        # ----------------------------------------------------
        # SELECT FIRST ATTACHMENT TYPE
        # ----------------------------------------------------

        self.ui.choose_attachment_type(
            attachment_type
        )

        # ----------------------------------------------------
        # SELECT FIRST FILE
        # ----------------------------------------------------

        print(
            "[ATTACHMENT] Selecting first file...",
            flush=True,
        )

        self._add_file_using_picker(
            first_file
        )

        # ----------------------------------------------------
        # ADD ALL REMAINING FILES
        #
        # IMPORTANT:
        # We do NOT reopen the attachment menu.
        #
        # We use:
        #
        #     +
        #     -> Windows Open
        #     -> file
        #
        # ----------------------------------------------------

        for index in range(
            1,
            len(file_paths),
        ):

            next_file = file_paths[index]

            print()
            print(
                "=" * 60,
                flush=True,
            )

            print(
                f"[ATTACHMENT] Adding file "
                f"{index + 1}/{len(file_paths)}",
                flush=True,
            )

            print(
                f"[ATTACHMENT] {next_file}",
                flush=True,
            )

            # Click + in attachment preview
            self._click_attachment_plus()

            # Same Windows Open file selection
            self._add_file_using_picker(
                next_file
            )

        # ----------------------------------------------------
        # WAIT FOR COMPLETE PREVIEW
        # ----------------------------------------------------

        print(
            "[ATTACHMENT] Waiting for all files "
            "to appear in preview...",
            flush=True,
        )

        time.sleep(1.5)

        # ----------------------------------------------------
        # ONE CAPTION FOR THE WHOLE ATTACHMENT BATCH
        # ----------------------------------------------------

        self._enter_caption(message)

        # ----------------------------------------------------
        # SEND ALL FILES TOGETHER
        # ----------------------------------------------------

        print()
        print(
            f"[ATTACHMENT] Sending "
            f"{len(file_paths)} file(s)...",
            flush=True,
        )

        send_success = (
            self._click_attachment_send()
        )

        if not send_success:
            raise RuntimeError(
                "WhatsApp attachment Send "
                "button could not be clicked."
            )

        time.sleep(1.0)

        print(
            f"[ATTACHMENT] "
            f"{len(file_paths)} file(s) sent",
            flush=True,
        )

        return {
            "success": True,
            "chat": selected_chat,
            "files": file_paths,
            # Kept for compatibility with old single-file code.
            "file": file_paths[0],
            "message": message,
            "type": attachment_type,
            "count": len(file_paths),
        }


# ============================================================
# PUBLIC TOOL
# ============================================================

class WhatsAppTool:

    def __init__(self):

        self.connection = (
            WhatsAppConnection()
        )

        self.ui = (
            WhatsAppUI(
                self.connection
            )
        )

        self.messages = (
            WhatsAppMessage(
                self.connection,
                self.ui
            )
        )

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    def connect(self):
        return self.connection.connect()

    # --------------------------------------------------------
    # SEND MESSAGE
    # --------------------------------------------------------

    def send_message(
        self,
        contact: str,
        message: str,
    ):

        return self.messages.send(
            contact,
            message,
        )

    # --------------------------------------------------------
    # READ MESSAGES
    # --------------------------------------------------------

    def read_messages(
        self,
        contact: str,
        save_screenshot: bool = True,
    ):

        return self.messages.read_messages(
            contact,
            save_screenshot,
        )


    # --------------------------------------------------------
    # SEND ATTACHMENT(S)
    # --------------------------------------------------------

    def send_attachment(
        self,
        contact: str,
        message: str,
        file_path: Union[
            str,
            Path,
            list[str],
            tuple[str, ...],
        ],
    ):

        return self.messages.send_attachment(
            contact,
            message,
            file_path,
        )


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("WHATSAPP TOOL TEST")
    print("=" * 60)

    whatsapp = WhatsAppTool()

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    print()
    print("Connecting to WhatsApp...")

    if not whatsapp.connect():

        print(
            "❌ WhatsApp Desktop not found."
        )

        raise SystemExit(1)

    print(
        "✅ WhatsApp connected"
    )

    # --------------------------------------------------------
    # SELECT OPERATION
    # --------------------------------------------------------

    print()
    print("Select operation:")
    print()
    print("1. Send message")
    print("2. Send attachment(s)")
    print("3. Read visible messages")
    print("q. Quit")
    print()

    operation = input(
        "Choice: "
    ).strip().lower()

    # ========================================================
    # SEND MESSAGE
    # ========================================================

    if operation == "1":

        print()
        print("=" * 60)
        print("SEND MESSAGE")
        print("=" * 60)

        contact = input(
            "Enter WhatsApp chat name: "
        ).strip()

        message = input(
            "Enter message: "
        )

        try:

            result = whatsapp.send_message(
                contact,
                message,
            )

            print()
            print("=" * 60)
            print("✅ MESSAGE SENT")
            print("=" * 60)

            print(
                f"Chat    : {result['chat']}"
            )

            print(
                f"Message : {result['message']}"
            )

        except Exception as exc:

            print()
            print("=" * 60)
            print("❌ MESSAGE FAILED")
            print("=" * 60)

            print(
                f"Reason: {exc}"
            )

    # ========================================================
    # SEND ATTACHMENT(S)
    # ========================================================

    elif operation == "2":

        print()
        print("=" * 60)
        print("SEND ATTACHMENT(S)")
        print("=" * 60)

        contact = input(
            "Enter WhatsApp chat name: "
        ).strip()

        message = input(
            "Enter message/caption: "
        )

        print()
        print(
            "Enter file paths one by one."
        )

        print(
            "Press ENTER on an empty line when finished."
        )

        file_paths = []

        while True:

            path = input(
                f"File {len(file_paths) + 1}: "
            ).strip()

            if not path:
                break

            file_paths.append(path)

        if not file_paths:

            print(
                "❌ No files selected."
            )

        else:

            try:

                result = (
                    whatsapp.send_attachment(
                        contact,
                        message,
                        file_paths,
                    )
                )

                print()
                print("=" * 60)
                print("✅ ATTACHMENTS SENT")
                print("=" * 60)

                print(
                    f"Chat    : {result['chat']}"
                )

                print(
                    f"Count   : {result['count']}"
                )

                print(
                    f"Caption : {result['message']}"
                )

                print()
                print("Files:")

                for index, path in enumerate(
                    result["files"],
                    start=1,
                ):
                    print(
                        f"{index}. {path}"
                    )

            except Exception as exc:

                print()
                print("=" * 60)
                print("❌ ATTACHMENT FAILED")
                print("=" * 60)

                print(
                    f"Reason: {exc}"
                )

    # ========================================================
    # READ MESSAGES
    # ========================================================

    elif operation == "3":

        print()
        print("=" * 60)
        print("READ VISIBLE WHATSAPP MESSAGES")
        print("=" * 60)

        contact = input(
            "Enter WhatsApp chat name: "
        ).strip()

        try:
            result = whatsapp.read_messages(
                contact,
                save_screenshot=True,
            )

            print()
            print("=" * 60)
            print("OCR RESULT")
            print("=" * 60)

            if result["text"]:
                print(result["text"])
            else:
                print("No readable message text found on screen.")

            print()
            print(
                f"[OCR] Lines detected: {result['count']}"
            )
            print(
                f"[OCR] Time: {result['ocr_seconds']:.2f} seconds"
            )

            if result.get("screenshot"):
                print(
                    f"[OCR] Screenshot: {result['screenshot']}"
                )

        except Exception as exc:

            print()
            print("=" * 60)
            print("OCR READ FAILED")
            print("=" * 60)
            print(f"Reason: {exc}")

    # ========================================================
    # QUIT
    # ========================================================

    elif operation == "q":

        print(
            "Operation cancelled."
        )

    # ========================================================
    # INVALID
    # ========================================================

    else:

        print(
            "Invalid choice."
        )

    print()
    print("=" * 60)
...