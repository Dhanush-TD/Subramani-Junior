import os

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
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

    All Google services use the same:
        google_token.json

    The token contains the complete Google API scopes.

    Behavior:

    1. Load existing google_token.json
    2. If access token is expired, refresh it
    3. If refresh token is invalid/revoked, start OAuth again
    4. Save the new credentials
    5. Return valid credentials
    """

    credentials = None

    # =====================================================
    # ALWAYS USE THE COMPLETE GOOGLE SCOPE LIST
    # =====================================================

    scopes = GOOGLE_SCOPES

    # =====================================================
    # CHECK CREDENTIALS FILE
    # =====================================================

    if not os.path.exists(CREDENTIALS_FILE):

        raise FileNotFoundError(
            f"Google credentials not found: "
            f"{CREDENTIALS_FILE}"
        )

    # =====================================================
    # LOAD EXISTING TOKEN
    # =====================================================

    if os.path.exists(TOKEN_FILE):

        try:

            credentials = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                scopes
            )

        except Exception as e:

            print(
                "Could not load existing Google token."
            )

            print(
                f"Token error: {e}"
            )

            credentials = None

    # =====================================================
    # REFRESH EXPIRED ACCESS TOKEN
    # =====================================================

    if credentials and credentials.expired:

        if credentials.refresh_token:

            try:

                print(
                    "Google access token expired."
                )

                print(
                    "Refreshing Google access token..."
                )

                credentials.refresh(
                    Request()
                )

                print(
                    "Google access token refreshed successfully."
                )

                # -----------------------------------------
                # Save refreshed credentials
                # -----------------------------------------

                with open(
                    TOKEN_FILE,
                    "w",
                    encoding="utf-8"
                ) as token:

                    token.write(
                        credentials.to_json()
                    )

            except RefreshError as e:

                # -----------------------------------------
                # Refresh token is expired/revoked
                # -----------------------------------------

                print(
                    "Google refresh token is expired "
                    "or revoked."
                )

                print(
                    f"Refresh error: {e}"
                )

                print(
                    "Starting Google OAuth authentication again..."
                )

                credentials = None

            except Exception as e:

                print(
                    "Unexpected error while refreshing "
                    "Google credentials."
                )

                print(
                    f"Refresh error: {e}"
                )

                credentials = None

        else:

            print(
                "Google access token expired and "
                "no refresh token is available."
            )

            credentials = None

    # =====================================================
    # AUTHENTICATION REQUIRED
    # =====================================================

    if not credentials or not credentials.valid:

        print(
            "Google authentication required."
        )

        print(
            "Opening browser for Google OAuth..."
        )

        # -------------------------------------------------
        # Create OAuth flow
        # -------------------------------------------------

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes
        )

        # -------------------------------------------------
        # Run local OAuth server
        # -------------------------------------------------

        credentials = flow.run_local_server(
            port=0
        )

        # =================================================
        # SAVE NEW TOKEN
        # =================================================

        with open(
            TOKEN_FILE,
            "w",
            encoding="utf-8"
        ) as token:

            token.write(
                credentials.to_json()
            )

        print(
            "Google authentication successful."
        )

        print(
            f"New Google token saved to: {TOKEN_FILE}"
        )

    # =====================================================
    # FINAL VALIDATION
    # =====================================================

    if not credentials or not credentials.valid:

        raise RuntimeError(
            "Google authentication failed. "
            "Valid credentials could not be obtained."
        )

    return credentials