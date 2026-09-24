import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


# =========================================================
# GOOGLE AUTHENTICATION CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json"
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "google_token.json"
)


# =========================================================
# ALL GOOGLE API SCOPES
# =========================================================

GOOGLE_SCOPES = [

    # -----------------------------------------------------
    # Gmail
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",

    # -----------------------------------------------------
    # Calendar
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/calendar",

    # -----------------------------------------------------
    # Drive
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/drive",

    # -----------------------------------------------------
    # Docs
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/documents",

    # -----------------------------------------------------
    # Sheets
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/spreadsheets",

    # -----------------------------------------------------
    # Tasks
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/tasks",

    # -----------------------------------------------------
    # Contacts / People
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/contacts.readonly",

    # -----------------------------------------------------
    # Google Meet
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/meetings.space.created",

    # -----------------------------------------------------
    # Google Chat
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/chat.messages",
    "https://www.googleapis.com/auth/chat.spaces",

    # -----------------------------------------------------
    # Drive Activity
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/drive.activity.readonly",

    # -----------------------------------------------------
    # Drive Labels
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/drive.labels.readonly",

    # -----------------------------------------------------
    # Forms
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",

    # -----------------------------------------------------
    # Slides
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/presentations",

    # -----------------------------------------------------
    # YouTube Data API
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/youtube.readonly",

    # -----------------------------------------------------
    # YouTube Analytics
    # -----------------------------------------------------
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


# =========================================================
# AUTHENTICATE GOOGLE ACCOUNT
# =========================================================

def get_google_credentials(scopes=None):
    """
    Authenticate the Google account once and reuse the
    same credentials for all Google APIs.

    Every Google service can call:

        get_google_credentials()

    The authentication token contains all Google scopes.
    """

    credentials = None

    # -----------------------------------------------------
    # Always use the complete Google scope list
    # -----------------------------------------------------

    scopes = GOOGLE_SCOPES

    # -----------------------------------------------------
    # Load existing token
    # -----------------------------------------------------

    if os.path.exists(TOKEN_FILE):

        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            scopes
        )

    # -----------------------------------------------------
    # Refresh expired token
    # -----------------------------------------------------

    if credentials and credentials.expired:

        if credentials.refresh_token:

            credentials.refresh(
                Request()
            )

    # -----------------------------------------------------
    # Authentication required
    # -----------------------------------------------------

    if not credentials or not credentials.valid:

        if not os.path.exists(CREDENTIALS_FILE):

            raise FileNotFoundError(
                f"Google credentials not found: "
                f"{CREDENTIALS_FILE}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes
        )

        credentials = flow.run_local_server(
            port=0
        )

        # -------------------------------------------------
        # Save token
        # -------------------------------------------------

        with open(
            TOKEN_FILE,
            "w",
            encoding="utf-8"
        ) as token:

            token.write(
                credentials.to_json()
            )

    return credentials