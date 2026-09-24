from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/presentations"
]


# =========================
# GOOGLE SLIDES SERVICE
# =========================

def get_slides_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "slides",
        "v1",
        credentials=credentials
    )

    return service


# =========================
# CREATE PRESENTATION
# =========================

@tool
def create_google_presentation(title: str):
    """
    Create a new Google Slides presentation.
    """

    service = get_slides_service()

    presentation = service.presentations().create(
        body={
            "title": title
        }
    ).execute()

    presentation_id = presentation["presentationId"]

    return {
        "presentation_id": presentation_id,
        "title": presentation.get("title", title),
        "url": f"https://docs.google.com/presentation/d/{presentation_id}/edit"
    }


# =========================
# READ PRESENTATION
# =========================

@tool
def read_google_presentation(presentation_id: str):
    """
    Read the basic structure and text from a Google Slides presentation.
    """

    service = get_slides_service()

    presentation = service.presentations().get(
        presentationId=presentation_id
    ).execute()

    slides = []

    for slide in presentation.get("slides", []):

        slide_data = {
            "slide_id": slide.get("objectId", ""),
            "text": []
        }

        for element in slide.get("pageElements", []):

            shape = element.get("shape")

            if not shape:
                continue

            text = shape.get("text")

            if not text:
                continue

            for text_element in text.get("textElements", []):

                text_run = text_element.get("textRun")

                if text_run:
                    content = text_run.get("content", "")

                    if content.strip():
                        slide_data["text"].append(content)

        slides.append(slide_data)

    return {
        "presentation_id": presentation.get(
            "presentationId", ""
        ),
        "title": presentation.get(
            "title", ""
        ),
        "url": f"https://docs.google.com/presentation/d/{presentation_id}/edit",
        "slides": slides
    }


# =========================
# ADD SLIDE
# =========================

@tool
def add_google_slide(
    presentation_id: str,
    layout: str = "BLANK"
):
    """
    Add a new slide to a Google Slides presentation.

    Supported layouts include:
    BLANK
    TITLE
    TITLE_AND_BODY
    TITLE_ONLY
    """

    service = get_slides_service()

    slide_id = f"slide_{len(presentation_id)}"

    request = {
        "createSlide": {
            "objectId": slide_id,
            "slideLayoutReference": {
                "predefinedLayout": layout
            }
        }
    }

    result = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={
            "requests": [request]
        }
    ).execute()

    return {
        "message": "Slide added successfully.",
        "slide_id": slide_id,
        "result": result
    }


# =========================
# INSERT TEXT
# =========================

@tool
def insert_text_into_slide(
    presentation_id: str,
    page_object_id: str,
    shape_object_id: str,
    text: str
):
    """
    Insert text into an existing text shape on a slide.

    page_object_id:
        Slide object ID.

    shape_object_id:
        Text box/shape object ID.
    """

    service = get_slides_service()

    requests = [
        {
            "insertText": {
                "objectId": shape_object_id,
                "insertionIndex": 0,
                "text": text
            }
        }
    ]

    result = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={
            "requests": requests
        }
    ).execute()

    return {
        "message": "Text inserted successfully.",
        "slide_id": page_object_id,
        "result": result
    }


# =========================
# CREATE TEXT BOX
# =========================

@tool
def create_text_box_on_slide(
    presentation_id: str,
    slide_id: str,
    text: str,
    x: int = 100,
    y: int = 100,
    width: int = 400,
    height: int = 100
):
    """
    Create a text box on a Google Slide.

    Coordinates and dimensions are in points.
    """

    service = get_slides_service()

    shape_id = f"textbox_{slide_id}_{x}_{y}"

    requests = [
        {
            "createShape": {
                "objectId": shape_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {
                            "magnitude": width,
                            "unit": "PT"
                        },
                        "height": {
                            "magnitude": height,
                            "unit": "PT"
                        }
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": x,
                        "translateY": y,
                        "unit": "PT"
                    }
                }
            }
        },
        {
            "insertText": {
                "objectId": shape_id,
                "insertionIndex": 0,
                "text": text
            }
        }
    ]

    result = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={
            "requests": requests
        }
    ).execute()

    return {
        "message": "Text box created successfully.",
        "shape_id": shape_id,
        "result": result
    }


# =========================
# DELETE SLIDE
# =========================

@tool
def delete_google_slide(
    presentation_id: str,
    slide_id: str
):
    """
    Delete a slide from a Google Slides presentation.
    """

    service = get_slides_service()

    requests = [
        {
            "deleteObject": {
                "objectId": slide_id
            }
        }
    ]

    service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={
            "requests": requests
        }
    ).execute()

    return "Slide deleted successfully."


# =========================
# EXPORT TOOLS
# =========================

google_slides_tools = [
    create_google_presentation,
    read_google_presentation,
    add_google_slide,
    insert_text_into_slide,
    create_text_box_on_slide,
    delete_google_slide,
]