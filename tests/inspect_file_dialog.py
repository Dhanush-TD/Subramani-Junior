from pywinauto import Desktop
import time


def inspect():

    print("=" * 80)
    print("WIN32 FILE DIALOG INSPECTOR")
    print("=" * 80)

    desktop = Desktop(backend="win32")

    windows = desktop.windows()

    print(f"\nTop-level windows: {len(windows)}")

    for i, window in enumerate(windows):

        try:
            if not window.is_visible():
                continue

            title = window.window_text()
            cls = window.class_name()
            handle = window.handle

            print("\n" + "-" * 80)
            print(f"[{i}]")
            print(f"Title  : {title!r}")
            print(f"Class  : {cls!r}")
            print(f"Handle : {handle}")

            # Inspect likely dialogs
            if (
                title.casefold() == "open"
                or cls == "#32770"
                or "file" in title.casefold()
            ):

                print("\n*** POSSIBLE FILE DIALOG ***")

                try:
                    children = window.descendants()

                    print(
                        f"Children: {len(children)}"
                    )

                    for j, child in enumerate(children):

                        try:
                            if not child.is_visible():
                                continue

                            print(
                                f"\n  [{j}]"
                            )

                            print(
                                f"    Text      : "
                                f"{child.window_text()!r}"
                            )

                            print(
                                f"    Class     : "
                                f"{child.class_name()!r}"
                            )

                            print(
                                f"    Handle    : "
                                f"{child.handle}"
                            )

                            try:
                                print(
                                    f"    Rectangle : "
                                    f"{child.rectangle()}"
                                )
                            except Exception:
                                pass

                        except Exception as e:
                            print(
                                f"    ERROR: {e}"
                            )

                except Exception as e:
                    print(
                        f"  Child inspection error: {e}"
                    )

        except Exception as e:
            print(
                f"Window error: {e}"
            )


print("Waiting for file dialog...")
print()
print("1. Open WhatsApp")
print("2. Click attachment")
print("3. Click Document")
print("4. Leave the Windows Open dialog visible")
print()

while True:

    inspect()

    print("\nSleeping 3 seconds...\n")

    time.sleep(3)