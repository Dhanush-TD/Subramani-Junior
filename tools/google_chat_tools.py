from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/chat.messages",
    "https://www.googleapis.com/auth/chat.spaces",
]


# =========================
# GOOGLE CHAT SERVICE
# =========================

def get_chat_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "chat",
        "v1",
        credentials=credentials
    )

    return service


# =========================
# LIST SPACES
# =========================

@tool
def list_google_chat_spaces(page_size: int = 20):
    """
    List Google Chat spaces available to the user.
    """

    service = get_chat_service()

    page_size = min(max(page_size, 1), 100)

    result = service.spaces().list(
        pageSize=page_size
    ).execute()

    spaces = result.get("spaces", [])

    if not spaces:
        return "No Google Chat spaces found."

    return [
        {
            "name": space.get("name", ""),
            "display_name": space.get("displayName", ""),
            "space_type": space.get("spaceType", ""),
        }
        for space in spaces
    ]


# =========================
# GET SPACE
# =========================

@tool
def get_google_chat_space(space_name: str):
    """
    Get information about a Google Chat space.

    Example:
    spaces/AAAA1234
    """

    service = get_chat_service()

    space = service.spaces().get(
        name=space_name
    ).execute()

    return space


# =========================
# LIST MESSAGES
# =========================

@tool
def list_google_chat_messages(
    space_name: str,
    page_size: int = 20
):
    """
    List messages from a Google Chat space.
    """

    service = get_chat_service()

    page_size = min(max(page_size, 1), 100)

    result = service.spaces().messages().list(
        parent=space_name,
        pageSize=page_size
    ).execute()

    messages = result.get("messages", [])

    if not messages:
        return "No messages found."

    return [
        {
            "name": message.get("name", ""),
            "text": message.get("text", ""),
            "create_time": message.get("createTime", ""),
            "sender": message.get("sender", {})
        }
        for message in messages
    ]


# =========================
# SEND MESSAGE
# =========================

@tool
def send_google_chat_message(
    space_name: str,
    text: str
):
    """
    Send a text message to a Google Chat space.
    """

    service = get_chat_service()

    message = service.spaces().messages().create(
        parent=space_name,
        body={
            "text": text
        }
    ).execute()

    return {
        "message_name": message.get("name", ""),
        "text": message.get("text", ""),
        "create_time": message.get("createTime", "")
    }


# =========================
# GET MESSAGE
# =========================

@tool
def get_google_chat_message(message_name: str):
    """
    Get a specific Google Chat message.

    Example:
    spaces/AAAA1234/messages/BBBB5678
    """

    service = get_chat_service()

    message = service.spaces().messages().get(
        name=message_name
    ).execute()

    return message


# =========================
# UPDATE MESSAGE
# =========================

@tool
def update_google_chat_message(
    message_name: str,
    text: str
):
    """
    Update a Google Chat message.
    """

    service = get_chat_service()

    message = service.spaces().messages().patch(
        name=message_name,
        updateMask="text",
        body={
            "text": text
        }
    ).execute()

    return {
        "message_name": message.get("name", ""),
        "text": message.get("text", "")
    }


# =========================
# DELETE MESSAGE
# =========================

@tool
def delete_google_chat_message(message_name: str):
    """
    Delete a Google Chat message.
    """

    service = get_chat_service()

    service.spaces().messages().delete(
        name=message_name
    ).execute()

    return "Google Chat message deleted successfully."


# =========================
# EXPORT TOOLS
# =========================

google_chat_tools = [
    list_google_chat_spaces,
    get_google_chat_space,
    list_google_chat_messages,
    send_google_chat_message,
    get_google_chat_message,
    update_google_chat_message,
    delete_google_chat_message,
]