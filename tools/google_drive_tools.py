import os
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================================================
# GOOGLE DRIVE CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)




# =========================================================
# DRIVE PERMISSIONS
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/drive"
]


# =========================================================
# GOOGLE DRIVE SERVICE
# =========================================================

def get_drive_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "drive",
        "v3",
        credentials=credentials
    )

    return service

# =========================================================
# LIST DRIVE FILES
# =========================================================

@tool
def list_drive_files(count: int = 20):
    """
    List recent files in Google Drive.
    """

    try:

        count = max(
            1,
            min(count, 50)
        )

        service = get_drive_service()

        result = service.files().list(
            pageSize=count,
            fields=(
                "files("
                "id,"
                "name,"
                "mimeType,"
                "size,"
                "modifiedTime,"
                "webViewLink"
                ")"
            ),
            orderBy="modifiedTime desc"
        ).execute()

        files = result.get(
            "files",
            []
        )

        if not files:

            return "No files found in Google Drive."

        output = []

        for file in files:

            size = file.get(
                "size",
                "N/A"
            )

            output.append(
                f"Name: {file.get('name')}\n"
                f"ID: {file.get('id')}\n"
                f"Type: {file.get('mimeType')}\n"
                f"Size: {size}\n"
                f"Modified: {file.get('modifiedTime')}"
            )

        return "\n\n".join(output)

    except Exception as e:

        return f"Failed to list Drive files: {e}"


# =========================================================
# SEARCH DRIVE FILES
# =========================================================

@tool
def search_drive_files(query: str, count: int = 20):
    """
    Search Google Drive files by name.

    Example:
    resume
    project
    python
    """

    if not query or not query.strip():

        return "Drive search failed: query cannot be empty."

    try:

        count = max(
            1,
            min(count, 50)
        )

        service = get_drive_service()

        escaped_query = query.strip().replace(
            "'",
            "\\'"
        )

        result = service.files().list(
            q=(
                "trashed = false and "
                f"name contains '{escaped_query}'"
            ),
            pageSize=count,
            fields=(
                "files("
                "id,"
                "name,"
                "mimeType,"
                "size,"
                "modifiedTime,"
                "webViewLink"
                ")"
            ),
            orderBy="modifiedTime desc"
        ).execute()

        files = result.get(
            "files",
            []
        )

        if not files:

            return (
                f"No Drive files found for: "
                f"{query}"
            )

        output = []

        for file in files:

            output.append(
                f"Name: {file.get('name')}\n"
                f"ID: {file.get('id')}\n"
                f"Type: {file.get('mimeType')}\n"
                f"Modified: {file.get('modifiedTime')}"
            )

        return "\n\n".join(output)

    except Exception as e:

        return f"Failed to search Drive: {e}"


# =========================================================
# GET DRIVE FILE
# =========================================================

@tool
def get_drive_file(file_id: str):
    """
    Get detailed information about a Google Drive file.
    """

    if not file_id or not file_id.strip():

        return "Drive file lookup failed: file ID cannot be empty."

    try:

        service = get_drive_service()

        file = service.files().get(
            fileId=file_id.strip(),
            fields=(
                "id,"
                "name,"
                "mimeType,"
                "size,"
                "createdTime,"
                "modifiedTime,"
                "webViewLink,"
                "description,"
                "parents"
            )
        ).execute()

        return (
            f"Name: {file.get('name')}\n"
            f"ID: {file.get('id')}\n"
            f"Type: {file.get('mimeType')}\n"
            f"Size: {file.get('size', 'N/A')}\n"
            f"Created: {file.get('createdTime')}\n"
            f"Modified: {file.get('modifiedTime')}\n"
            f"Link: {file.get('webViewLink', 'N/A')}\n"
            f"Description: {file.get('description', '')}"
        )

    except Exception as e:

        return f"Failed to get Drive file: {e}"


# =========================================================
# DOWNLOAD DRIVE FILE
# =========================================================

@tool
def download_drive_file(
    file_id: str,
    save_dir: str = ""
):
    """
    Download a Google Drive file to the local computer.
    """

    if not file_id or not file_id.strip():

        return (
            "Drive download failed: "
            "file ID cannot be empty."
        )

    try:

        service = get_drive_service()

        # -------------------------------------------------
        # Default Downloads folder
        # -------------------------------------------------

        if not save_dir:

            save_dir = os.path.join(
                os.path.expanduser("~"),
                "Downloads"
            )

        os.makedirs(
            save_dir,
            exist_ok=True
        )

        # -------------------------------------------------
        # Get file metadata
        # -------------------------------------------------

        file = service.files().get(
            fileId=file_id.strip(),
            fields="name,mimeType"
        ).execute()

        filename = file.get(
            "name",
            "downloaded_file"
        )

        mime_type = file.get(
            "mimeType",
            ""
        )

        file_path = os.path.join(
            save_dir,
            filename
        )

        # -------------------------------------------------
        # Google Workspace files
        # -------------------------------------------------

        export_types = {
            "application/vnd.google-apps.document":
                (
                    "application/pdf",
                    ".pdf"
                ),

            "application/vnd.google-apps.spreadsheet":
                (
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet",
                    ".xlsx"
                ),

            "application/vnd.google-apps.presentation":
                (
                    "application/vnd.openxmlformats-officedocument"
                    ".presentationml.presentation",
                    ".pptx"
                )
        }

        if mime_type in export_types:

            export_mime, extension = export_types[
                mime_type
            ]

            if not filename.lower().endswith(
                extension
            ):

                filename += extension

            file_path = os.path.join(
                save_dir,
                filename
            )

            request = service.files().export_media(
                fileId=file_id.strip(),
                mimeType=export_mime
            )

        else:

            request = service.files().get_media(
                fileId=file_id.strip()
            )

        # -------------------------------------------------
        # Download
        # -------------------------------------------------

        with open(
            file_path,
            "wb"
        ) as file_handle:

            downloader = MediaIoBaseDownload(
                file_handle,
                request
            )

            done = False

            while not done:

                status, done = downloader.next_chunk()

        return (
            "Drive file downloaded successfully.\n"
            f"File: {filename}\n"
            f"Location: {file_path}"
        )

    except Exception as e:

        return (
            f"Failed to download Drive file: {e}"
        )


# =========================================================
# UPLOAD DRIVE FILE
# =========================================================

@tool
def upload_drive_file(
    file_path: str,
    folder_id: str = ""
):
    """
    Upload a local file to Google Drive.

    folder_id is optional.
    """

    if not file_path or not file_path.strip():

        return (
            "Drive upload failed: "
            "file path cannot be empty."
        )

    file_path = os.path.abspath(
        file_path.strip()
    )

    if not os.path.exists(file_path):

        return (
            f"Drive upload failed: "
            f"file not found: {file_path}"
        )

    try:

        service = get_drive_service()

        metadata = {
            "name": os.path.basename(
                file_path
            )
        }

        if folder_id and folder_id.strip():

            metadata["parents"] = [
                folder_id.strip()
            ]

        media = MediaFileUpload(
            file_path,
            resumable=True
        )

        result = service.files().create(
            body=metadata,
            media_body=media,
            fields=(
                "id,"
                "name,"
                "mimeType,"
                "webViewLink"
            )
        ).execute()

        return (
            "File uploaded successfully.\n"
            f"Name: {result.get('name')}\n"
            f"ID: {result.get('id')}\n"
            f"Link: {result.get('webViewLink', 'N/A')}"
        )

    except Exception as e:

        return (
            f"Failed to upload Drive file: {e}"
        )