import os

from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/documents"
]


# =========================
# GOOGLE DOCS SERVICE
# =========================

def get_docs_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "docs",
        "v1",
        credentials=credentials
    )

    return service


# =========================
# CREATE DOCUMENT
# =========================

@tool
def create_google_doc(title: str):
    """
    Create a new Google Doc with the given title.
    Returns the document ID and URL.
    """

    service = get_docs_service()

    document = service.documents().create(
        body={
            "title": title
        }
    ).execute()

    document_id = document["documentId"]

    return {
        "document_id": document_id,
        "title": document.get("title", title),
        "url": f"https://docs.google.com/document/d/{document_id}/edit"
    }


# =========================
# READ DOCUMENT
# =========================

@tool
def read_google_doc(document_id: str):
    """
    Read the text content of a Google Doc using its document ID.
    """

    service = get_docs_service()

    document = service.documents().get(
        documentId=document_id
    ).execute()

    content = document.get("body", {}).get("content", [])

    text = []

    for element in content:

        paragraph = element.get("paragraph")

        if paragraph:
            for item in paragraph.get("elements", []):

                text_run = item.get("textRun")

                if text_run:
                    text.append(
                        text_run.get("content", "")
                    )

    return "".join(text)


# =========================
# APPEND TEXT TO DOCUMENT
# =========================

@tool
def append_to_google_doc(document_id: str, text: str):
    """
    Append text to the end of an existing Google Doc.
    """

    service = get_docs_service()

    document = service.documents().get(
        documentId=document_id
    ).execute()

    end_index = document["body"]["content"][-1]["endIndex"] - 1

    requests = [
        {
            "insertText": {
                "location": {
                    "index": end_index
                },
                "text": text
            }
        }
    ]

    service.documents().batchUpdate(
        documentId=document_id,
        body={
            "requests": requests
        }
    ).execute()

    return "Text appended successfully."


# =========================
# INSERT TEXT AT POSITION
# =========================

@tool
def insert_text_into_google_doc(
    document_id: str,
    text: str,
    index: int
):
    """
    Insert text at a specific index in a Google Doc.
    """

    service = get_docs_service()

    requests = [
        {
            "insertText": {
                "location": {
                    "index": index
                },
                "text": text
            }
        }
    ]

    service.documents().batchUpdate(
        documentId=document_id,
        body={
            "requests": requests
        }
    ).execute()

    return "Text inserted successfully."


# =========================
# REPLACE TEXT
# =========================

@tool
def replace_text_in_google_doc(
    document_id: str,
    old_text: str,
    new_text: str
):
    """
    Replace all occurrences of text in a Google Doc.
    """

    service = get_docs_service()

    requests = [
        {
            "replaceAllText": {
                "containsText": {
                    "text": old_text,
                    "matchCase": True
                },
                "replaceText": new_text
            }
        }
    ]

    result = service.documents().batchUpdate(
        documentId=document_id,
        body={
            "requests": requests
        }
    ).execute()

    occurrences = 0

    replies = result.get("replies", [])

    for reply in replies:
        replace_result = reply.get(
            "replaceAllText",
            {}
        )

        occurrences += replace_result.get(
            "occurrencesChanged",
            0
        )

    return f"Replaced {occurrences} occurrence(s)."


# =========================
# DELETE TEXT
# =========================

@tool
def delete_text_from_google_doc(
    document_id: str,
    start_index: int,
    end_index: int
):
    """
    Delete text between two indexes in a Google Doc.
    """

    service = get_docs_service()

    requests = [
        {
            "deleteContentRange": {
                "range": {
                    "startIndex": start_index,
                    "endIndex": end_index
                }
            }
        }
    ]

    service.documents().batchUpdate(
        documentId=document_id,
        body={
            "requests": requests
        }
    ).execute()

    return "Text deleted successfully."


# =========================
# EXPORT TOOLS
# =========================

google_docs_tools = [
    create_google_doc,
    read_google_doc,
    append_to_google_doc,
    insert_text_into_google_doc,
    replace_text_in_google_doc,
    delete_text_from_google_doc,
]