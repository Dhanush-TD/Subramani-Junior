from tools.whatsapp_tools import (
    open_whatsapp,
    close_whatsapp,
    search_whatsapp_contact,
    send_whatsapp_message,
    send_whatsapp_file,
)


def test_open_whatsapp():
    print("\n--- TEST: OPEN WHATSAPP ---")

    result = open_whatsapp()

    print("RESULT:", result)


def test_search_contact():
    print("\n--- TEST: SEARCH CONTACT ---")

    result = search_whatsapp_contact(
        contact_name="Bharath AIDS"
    )

    print("RESULT:", result)


def test_send_message():
    print("\n--- TEST: SEND MESSAGE ---")

    result = send_whatsapp_message(
        contact_name="Bharath AIDS",
        message="Hello, this is a WhatsApp automation test."
    )

    print("RESULT:", result)


def test_send_file():
    print("\n--- TEST: SEND FILE ---")

    file_path = r"C:\Users\Dhanush\Desktop\test.txt"

    result = send_whatsapp_file(
        contact_name="Bharath AIDS",
        file_path=file_path
    )

    print("RESULT:", result)


def test_close_whatsapp():
    print("\n--- TEST: CLOSE WHATSAPP ---")

    result = close_whatsapp()

    print("RESULT:", result)


if __name__ == "__main__":

    print("==========================================")
    print(" WhatsApp Tools Test")
    print("==========================================")

    # Test one at a time first.

    test_open_whatsapp()

    input("\nPress ENTER after checking WhatsApp...")

    test_search_contact()

    input("\nPress ENTER after checking contact...")

    test_send_message()

    input("\nPress ENTER after checking message...")

    test_send_file()

    input("\nPress ENTER after checking file...")

    test_close_whatsapp()

    print("\n==========================================")
    print(" WhatsApp testing completed.")
    print("==========================================")


if __name__ == "__main__":
    test_open_whatsapp()