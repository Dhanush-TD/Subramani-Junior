from pywinauto import Desktop


WHATSAPP_TITLE = "WhatsApp"
WHATSAPP_CLASS = "WinUIDesktopWin32WindowClass"


desktop = Desktop(backend="uia")

window = None

for w in desktop.windows():

    try:
        if (
            w.window_text().strip() == WHATSAPP_TITLE
            and w.class_name() == WHATSAPP_CLASS
        ):
            window = w
            break

    except Exception:
        pass


if window is None:
    print("WhatsApp not found")
    raise SystemExit


window.restore()
window.maximize()
window.set_focus()


print("=" * 80)
print("WHATSAPP SEARCH / CONTACT DIAGNOSTIC")
print("=" * 80)


# ------------------------------------------------------------
# EDIT CONTROLS
# ------------------------------------------------------------

print("\nEDIT CONTROLS")
print("-" * 80)

edits = window.descendants(control_type="Edit")

for i, edit in enumerate(edits):

    try:

        print(
            f"[{i}] "
            f"name={edit.element_info.name!r} "
            f"automation_id={edit.element_info.automation_id!r} "
            f"class={edit.element_info.class_name!r} "
            f"visible={edit.is_visible()} "
            f"enabled={edit.is_enabled()} "
            f"rect={edit.rectangle()}"
        )

    except Exception as e:

        print(
            f"[{i}] ERROR: {e}"
        )


# ------------------------------------------------------------
# DATA ITEMS
# ------------------------------------------------------------

print("\nDATA ITEMS")
print("-" * 80)

items = window.descendants(
    control_type="DataItem"
)

for i, item in enumerate(items):

    try:

        if not item.is_visible():
            continue

        name = (
            item.element_info.name
            or ""
        )

        if not name:
            continue

        print(
            f"[{i}] "
            f"name={name!r} "
            f"automation_id={item.element_info.automation_id!r} "
            f"class={item.element_info.class_name!r} "
            f"rect={item.rectangle()}"
        )

    except Exception as e:

        print(
            f"[{i}] ERROR: {e}"
        )