import uiautomation as auto
import time

def get_whatsapp_window():
    wa_window = auto.WindowControl(searchDepth=1, Name="WhatsApp")
    if not wa_window.Exists(5):
        raise Exception("WhatsApp window not found.")
    wa_window.SetActive()
    time.sleep(0.5)
    return wa_window

def dump_tree_to_file(filename="wa_tree_dump.txt", max_depth=10):
    wa_window = get_whatsapp_window()

    with open(filename, "w", encoding="utf-8") as f:
        def recurse(ctrl, depth=0):
            indent = "  " * depth
            name = ctrl.Name or ""
            ctype = ctrl.ControlTypeName
            try:
                legacy = ctrl.GetLegacyIAccessiblePattern()
                legacy_val = legacy.Value if legacy else ""
            except Exception:
                legacy_val = ""

            line = f"{indent}[{ctype}] Name='{name}' LegacyValue='{legacy_val}'\n"
            f.write(line)

            if depth < max_depth:
                for child in ctrl.GetChildren():
                    recurse(child, depth + 1)

        recurse(wa_window)

    print(f"Tree dumped to {filename}")

if __name__ == "__main__":
    dump_tree_to_file()