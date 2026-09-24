from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]


# =========================
# GOOGLE FORMS SERVICE
# =========================

def get_forms_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "forms",
        "v1",
        credentials=credentials
    )

    return service


# =========================
# CREATE FORM
# =========================

@tool
def create_google_form(title: str, document_title: str = ""):
    """
    Create a new Google Form.
    """

    service = get_forms_service()

    body = {
        "info": {
            "title": title
        }
    }

    if document_title:
        body["info"]["documentTitle"] = document_title

    form = service.forms().create(
        body=body
    ).execute()

    form_id = form.get("formId", "")

    return {
        "form_id": form_id,
        "title": form.get("info", {}).get("title", title),
        "url": form.get(
            "responderUri",
            f"https://docs.google.com/forms/d/{form_id}/viewform"
        )
    }


# =========================
# GET FORM
# =========================

@tool
def get_google_form(form_id: str):
    """
    Get the details and questions of a Google Form.
    """

    service = get_forms_service()

    form = service.forms().get(
        formId=form_id
    ).execute()

    return form


# =========================
# LIST RESPONSES
# =========================

@tool
def list_google_form_responses(
    form_id: str,
    page_size: int = 20
):
    """
    List responses submitted to a Google Form.
    """

    service = get_forms_service()

    page_size = min(max(page_size, 1), 5000)

    result = service.forms().responses().list(
        formId=form_id,
        pageSize=page_size
    ).execute()

    responses = result.get("responses", [])

    if not responses:
        return "No responses found."

    return responses


# =========================
# GET RESPONSE
# =========================

@tool
def get_google_form_response(
    form_id: str,
    response_id: str
):
    """
    Get a specific Google Form response.
    """

    service = get_forms_service()

    response = service.forms().responses().get(
        formId=form_id,
        responseId=response_id
    ).execute()

    return response


# =========================
# ADD FORM QUESTION
# =========================

@tool
def add_google_form_question(
    form_id: str,
    question: str,
    required: bool = False
):
    """
    Add a simple text question to a Google Form.
    """

    service = get_forms_service()

    requests = [
        {
            "createItem": {
                "item": {
                    "title": question,
                    "questionItem": {
                        "question": {
                            "required": required,
                            "textQuestion": {
                                "paragraph": False
                            }
                        }
                    }
                },
                "location": {
                    "index": 0
                }
            }
        }
    ]

    result = service.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": requests
        }
    ).execute()

    return {
        "message": "Question added successfully.",
        "result": result
    }


# =========================
# EXPORT TOOLS
# =========================

google_forms_tools = [
    create_google_form,
    get_google_form,
    list_google_form_responses,
    get_google_form_response,
    add_google_form_question,
]