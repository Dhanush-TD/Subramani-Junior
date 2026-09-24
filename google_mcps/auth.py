import json
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import (
    OAuthClientMetadata,
    OAuthClientInformationFull,
    OAuthToken,
)

CREDENTIALS_FILE = Path("google_mcp_credentials.json")
TOKEN_FILE = Path("google_mcp_token.json")
CLIENT_INFO_FILE = Path("google_mcp_client.json")

REDIRECT_URI = "http://localhost:3030/callback"
CALENDAR_MCP_URL = "https://calendarmcp.googleapis.com/mcp/v1"


class FileTokenStorage(TokenStorage):
    def __init__(self):
        self._tokens = None
        self._client_info = None

        # Load OAuth tokens if they exist
        if TOKEN_FILE.exists():
            try:
                data = json.loads(
                    TOKEN_FILE.read_text(encoding="utf-8")
                )

                if data:
                    self._tokens = OAuthToken.model_validate(data)

            except Exception as e:
                print(f"Warning: Could not load OAuth token: {e}")

        # Load OAuth client information if it exists
        if CLIENT_INFO_FILE.exists():
            try:
                data = json.loads(
                    CLIENT_INFO_FILE.read_text(encoding="utf-8")
                )

                if data:
                    self._client_info = (
                        OAuthClientInformationFull.model_validate(data)
                    )

            except Exception as e:
                print(
                    f"Warning: Could not load OAuth client information: {e}"
                )

    async def get_tokens(self):
        return self._tokens

    async def set_tokens(self, tokens):
        self._tokens = tokens

        TOKEN_FILE.write_text(
            json.dumps(
                tokens.model_dump(mode="json"),
                indent=2,
            ),
            encoding="utf-8",
        )

    async def get_client_info(self):
        return self._client_info

    async def set_client_info(self, client_info):
        self._client_info = client_info

        CLIENT_INFO_FILE.write_text(
            json.dumps(
                client_info.model_dump(mode="json"),
                indent=2,
            ),
            encoding="utf-8",
        )


def load_credentials():
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Google MCP credentials file not found: "
            f"{CREDENTIALS_FILE.resolve()}"
        )

    with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "web" not in data:
        raise ValueError(
            "google_mcp_credentials.json must contain a 'web' section."
        )

    return data["web"]


def create_google_oauth_provider():

    credentials = load_credentials()

    client_metadata = OAuthClientMetadata(
        redirect_uris=[REDIRECT_URI],
        token_endpoint_auth_method="client_secret_post",
        grant_types=[
            "authorization_code",
            "refresh_token",
        ],
        response_types=["code"],
    )

    storage = FileTokenStorage()

    # If we already have Google MCP client credentials,
    # construct the MCP client information so the SDK
    # does not try dynamic client registration (/register).
    if storage._client_info is None:

        storage._client_info = OAuthClientInformationFull(
            redirect_uris=[REDIRECT_URI],
            token_endpoint_auth_method="client_secret_post",
            grant_types=[
                "authorization_code",
                "refresh_token",
            ],
            response_types=["code"],
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
        )

    async def redirect_handler(authorization_url: str):
        print("\nOpening Google authorization page...")
        print(authorization_url)

        webbrowser.open(authorization_url)

    async def callback_handler():
        print("\nWaiting for Google OAuth callback.")
        print("Paste the FULL callback URL here:")

        callback_url = input("> ").strip()

        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)

        if "error" in params:
            raise RuntimeError(
                f"Google OAuth error: {params['error'][0]}"
            )

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]

        if not code:
            raise RuntimeError(
                "Authorization code not found in callback URL."
            )

        return code, state

    return OAuthClientProvider(
        server_url=CALENDAR_MCP_URL,
        client_metadata=client_metadata,
        storage=storage,
        redirect_handler=redirect_handler,
        callback_handler=callback_handler,
    )