from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/meetings.space.created"
]


# =========================
# GOOGLE MEET SERVICE
# =========================

def get_meet_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "meet",
        "v2",
        credentials=credentials
    )

    return service


# =========================
# CREATE MEETING SPACE
# =========================

@tool
def create_google_meeting():
    """
    Create a new Google Meet meeting space.
    Returns the meeting URI and meeting code.
    """

    service = get_meet_service()

    meeting_space = service.spaces().create(
        body={}
    ).execute()

    return {
        "name": meeting_space.get("name", ""),
        "meeting_uri": meeting_space.get("meetingUri", ""),
        "meeting_code": meeting_space.get("meetingCode", ""),
        "space": meeting_space
    }


# =========================
# GET MEETING SPACE
# =========================

@tool
def get_google_meeting_space(space_name: str):
    """
    Get information about an existing Google Meet space.

    Example:
    spaces/abc-defg-hij
    """

    service = get_meet_service()

    meeting_space = service.spaces().get(
        name=space_name
    ).execute()

    return meeting_space


# =========================
# END MEETING SPACE
# =========================

@tool
def end_google_meeting(space_name: str):
    """
    End an active Google Meet meeting space.
    """

    service = get_meet_service()

    meeting_space = service.spaces().endActiveConference(
        name=space_name,
        body={}
    ).execute()

    return {
        "message": "Active conference ended successfully.",
        "space": meeting_space
    }


# =========================
# EXPORT TOOLS
# =========================

google_meet_tools = [
    create_google_meeting,
    get_google_meeting_space,
    end_google_meeting,
]