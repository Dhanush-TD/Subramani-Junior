import os
import base64
import mimetypes

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google_auth import get_google_credentials
from googleapiclient.discovery import build

from langchain_core.tools import tool


# =========================================================
# GMAIL CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CREDENTIALS_FILE = os.path.join(
    BASE_DIR,
    "credentials.json"
)

TOKEN_FILE = os.path.join(
    BASE_DIR,
    "token.json"
)


# =========================================================
# GMAIL PERMISSIONS
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


# =========================================================
# TOKEN OPTIMIZATION
# =========================================================

# Maximum email body returned to the main LLM.
#
# This does NOT change the actual Gmail email.
# It only limits how much email content is passed back
# into the DeepSeek agent context.
MAX_EMAIL_BODY_CHARS = 8000


# =========================================================
# GMAIL SERVICE
# =========================================================
def get_gmail_service():
    credentials = get_google_credentials(SCOPES)

    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    return service
# =========================================================
# EXTRACT HEADER
# =========================================================

def get_header(headers, name):

    for header in headers:

        if header["name"].lower() == name.lower():

            return header["value"]

    return ""


# =========================================================
# EXTRACT MESSAGE BODY
# =========================================================

def extract_body(payload):

    # -----------------------------------------------------
    # Direct body
    # -----------------------------------------------------

    body = payload.get(
        "body",
        {}
    )

    data = body.get(
        "data"
    )

    if data:

        try:

            return base64.urlsafe_b64decode(
                data
            ).decode(
                "utf-8",
                errors="ignore"
            )

        except Exception:

            pass

    # -----------------------------------------------------
    # Multipart message
    # -----------------------------------------------------

    parts = payload.get(
        "parts",
        []
    )

    for part in parts:

        mime_type = part.get(
            "mimeType",
            ""
        )

        if mime_type == "text/plain":

            part_body = part.get(
                "body",
                {}
            )

            data = part_body.get(
                "data"
            )

            if data:

                try:

                    return base64.urlsafe_b64decode(
                        data
                    ).decode(
                        "utf-8",
                        errors="ignore"
                    )

                except Exception:

                    pass

        # -------------------------------------------------
        # Recursive multipart
        # -------------------------------------------------

        if part.get("parts"):

            result = extract_body(
                part
            )

            if result:

                return result

    return ""


# =========================================================
# OPTIMIZE EMAIL BODY
# =========================================================

def _limit_email_body(
    body: str,
    max_chars: int = MAX_EMAIL_BODY_CHARS,
) -> str:
    """
    Limit the amount of email content returned to the LLM.

    The original Gmail message is never modified.

    For large emails, keep both the beginning and end so
    important information near either side is retained.
    """

    if not body:

        return ""

    body = body.strip()

    if len(body) <= max_chars:

        return body

    # -----------------------------------------------------
    # Keep beginning + ending
    # -----------------------------------------------------

    head_size = max_chars // 2
    tail_size = max_chars - head_size

    return (
        body[:head_size]
        + "\n\n"
        "[EMAIL BODY TRUNCATED FOR TOKEN EFFICIENCY]\n"
        "[The original email is unchanged.]\n\n"
        + body[-tail_size:]
    )


# =========================================================
# FIND ATTACHMENTS RECURSIVELY
# =========================================================

def find_attachments(
    parts,
    results=None
):

    if results is None:

        results = []

    for part in parts:

        filename = part.get(
            "filename",
            ""
        )

        body = part.get(
            "body",
            {}
        )

        attachment_id = body.get(
            "attachmentId"
        )

        mime_type = part.get(
            "mimeType",
            ""
        )

        size = body.get(
            "size",
            0
        )

        # -------------------------------------------------
        # Normal Gmail attachment
        # -------------------------------------------------

        if filename:

            results.append({
                "filename": filename,
                "attachment_id": attachment_id,
                "mime_type": mime_type,
                "size": size,
                "body_data": body.get("data")
            })

        # -------------------------------------------------
        # Nested parts
        # -------------------------------------------------

        nested_parts = part.get(
            "parts",
            []
        )

        if nested_parts:

            find_attachments(
                nested_parts,
                results
            )

    return results


# =========================================================
# FIND ATTACHMENT BY NAME
# =========================================================

def find_attachment_by_name(
    attachments,
    attachment_name
):

    if not attachment_name:

        return None

    attachment_name = attachment_name.lower()

    # -----------------------------------------------------
    # Exact match first
    # -----------------------------------------------------

    for attachment in attachments:

        if (
            attachment["filename"].lower()
            == attachment_name
        ):

            return attachment

    # -----------------------------------------------------
    # Partial match second
    # -----------------------------------------------------

    for attachment in attachments:

        if (
            attachment_name
            in attachment["filename"].lower()
        ):

            return attachment

    return None


# =========================================================
# CHECK RECENT EMAILS
# =========================================================

@tool
def check_emails(count: int = 10):
    """
    Get the user's latest Gmail emails.

    Returns sender, subject, date and message ID.
    """

    try:

        # Keep the result set bounded.
        count = max(1, min(count, 10))

        service = get_gmail_service()

        result = service.users().messages().list(
            userId="me",
            maxResults=count
        ).execute()

        messages = result.get(
            "messages",
            []
        )

        if not messages:

            return "No emails found."

        output = []

        for message in messages:

            message_id = message["id"]

            email = service.users().messages().get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=[
                    "From",
                    "To",
                    "Subject",
                    "Date"
                ]
            ).execute()

            headers = email.get(
                "payload",
                {}
            ).get(
                "headers",
                []
            )

            sender = get_header(
                headers,
                "From"
            )

            subject = get_header(
                headers,
                "Subject"
            )

            date = get_header(
                headers,
                "Date"
            )

            output.append(
                f"ID: {message_id}\n"
                f"From: {sender}\n"
                f"Subject: {subject}\n"
                f"Date: {date}"
            )

        return "\n\n".join(
            output
        )

    except Exception as e:

        return (
            f"Failed to check emails: {e}"
        )


# =========================================================
# SEARCH EMAILS
# =========================================================

@tool
def search_emails(
    query: str,
    count: int = 10
):
    """
    Search Gmail using Gmail search syntax.

    Examples:
    from:github.com
    subject:invoice
    is:unread
    has:attachment
    filename:pdf
    """

    if not query or not query.strip():

        return "Email search failed: query cannot be empty."

    try:

        # Keep result set bounded.
        count = max(1, min(count, 10))

        service = get_gmail_service()

        result = service.users().messages().list(
            userId="me",
            q=query.strip(),
            maxResults=count
        ).execute()

        messages = result.get(
            "messages",
            []
        )

        if not messages:

            return (
                f"No emails found for: {query}"
            )

        output = []

        for message in messages:

            message_id = message["id"]

            email = service.users().messages().get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=[
                    "From",
                    "To",
                    "Subject",
                    "Date"
                ]
            ).execute()

            headers = email.get(
                "payload",
                {}
            ).get(
                "headers",
                []
            )

            sender = get_header(
                headers,
                "From"
            )

            subject = get_header(
                headers,
                "Subject"
            )

            date = get_header(
                headers,
                "Date"
            )

            output.append(
                f"ID: {message_id}\n"
                f"From: {sender}\n"
                f"Subject: {subject}\n"
                f"Date: {date}"
            )

        return "\n\n".join(
            output
        )

    except Exception as e:

        return (
            f"Failed to search emails: {e}"
        )


# =========================================================
# READ EMAIL
# =========================================================

@tool
def read_email(message_id: str):
    """
    Read a Gmail message using its message ID.

    Large email bodies are automatically limited before
    being returned to the main AI agent.
    """

    if not message_id or not message_id.strip():

        return "Email read failed: message ID cannot be empty."

    try:

        service = get_gmail_service()

        email = service.users().messages().get(
            userId="me",
            id=message_id.strip(),
            format="full"
        ).execute()

        payload = email.get(
            "payload",
            {}
        )

        headers = payload.get(
            "headers",
            []
        )

        sender = get_header(
            headers,
            "From"
        )

        recipient = get_header(
            headers,
            "To"
        )

        subject = get_header(
            headers,
            "Subject"
        )

        date = get_header(
            headers,
            "Date"
        )

        body = extract_body(
            payload
        )

        if not body:

            body = "[No plain-text body found]"

        # -------------------------------------------------
        # TOKEN OPTIMIZATION
        # -------------------------------------------------

        body = _limit_email_body(
            body
        )

        return (
            f"From: {sender}\n"
            f"To: {recipient}\n"
            f"Subject: {subject}\n"
            f"Date: {date}\n\n"
            f"{body}"
        )

    except Exception as e:

        return (
            f"Failed to read email: {e}"
        )


# =========================================================
# LIST EMAIL ATTACHMENTS
# =========================================================

@tool
def list_email_attachments(message_id: str):
    """
    Show all attachments in a Gmail message.

    Requires a Gmail message ID.
    """

    if not message_id or not message_id.strip():

        return (
            "Attachment listing failed: "
            "message ID cannot be empty."
        )

    try:

        service = get_gmail_service()

        email = service.users().messages().get(
            userId="me",
            id=message_id.strip(),
            format="full"
        ).execute()

        payload = email.get(
            "payload",
            {}
        )

        parts = payload.get(
            "parts",
            []
        )

        attachments = find_attachments(
            parts
        )

        if not attachments:

            return "No attachments found."

        output = []

        for index, attachment in enumerate(
            attachments,
            start=1
        ):

            filename = attachment["filename"]
            mime_type = attachment["mime_type"]
            size = attachment["size"]

            output.append(
                f"{index}. {filename}\n"
                f"Type: {mime_type}\n"
                f"Size: {size} bytes"
            )

        return "\n\n".join(
            output
        )

    except Exception as e:

        return (
            f"Failed to list attachments: {e}"
        )


# =========================================================
# DOWNLOAD EMAIL ATTACHMENT
# =========================================================

@tool
def download_email_attachment(
    message_id: str,
    attachment_name: str,
    save_dir: str = ""
):
    """
    Download an attachment from a Gmail message.

    The user only needs to provide the email message ID
    and attachment filename.
    """

    if not message_id or not message_id.strip():

        return (
            "Attachment download failed: "
            "message ID cannot be empty."
        )

    if not attachment_name or not attachment_name.strip():

        return (
            "Attachment download failed: "
            "attachment name cannot be empty."
        )

    try:

        service = get_gmail_service()

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
        # Get complete email
        # -------------------------------------------------

        email = service.users().messages().get(
            userId="me",
            id=message_id.strip(),
            format="full"
        ).execute()

        payload = email.get(
            "payload",
            {}
        )

        parts = payload.get(
            "parts",
            []
        )

        attachments = find_attachments(
            parts
        )

        if not attachments:

            return "No attachments found in this email."

        # -------------------------------------------------
        # Find requested attachment
        # -------------------------------------------------

        attachment = find_attachment_by_name(
            attachments,
            attachment_name.strip()
        )

        if not attachment:

            available = ", ".join(
                item["filename"]
                for item in attachments
            )

            return (
                f"Attachment '{attachment_name}' "
                f"was not found.\n"
                f"Available attachments: {available}"
            )

        filename = os.path.basename(
            attachment["filename"]
        )

        file_path = os.path.join(
            save_dir,
            filename
        )

        # -------------------------------------------------
        # Get attachment data
        # -------------------------------------------------

        data = attachment.get(
            "body_data"
        )

        # -------------------------------------------------
        # Normal Gmail attachment
        # -------------------------------------------------

        if attachment.get("attachment_id"):

            attachment_data = (
                service.users()
                .messages()
                .attachments()
                .get(
                    userId="me",
                    messageId=message_id.strip(),
                    id=attachment["attachment_id"]
                )
                .execute()
            )

            data = attachment_data.get(
                "data"
            )

        if not data:

            return (
                "Could not retrieve attachment data."
            )

        # -------------------------------------------------
        # Decode attachment
        # -------------------------------------------------

        file_data = base64.urlsafe_b64decode(
            data
        )

        # -------------------------------------------------
        # Save file
        # -------------------------------------------------

        with open(
            file_path,
            "wb"
        ) as file:

            file.write(
                file_data
            )

        return (
            "Attachment downloaded successfully.\n"
            f"File: {filename}\n"
            f"Location: {file_path}"
        )

    except Exception as e:

        return (
            f"Failed to download attachment: {e}"
        )


# =========================================================
# CREATE EMAIL WITH OPTIONAL ATTACHMENT
# =========================================================

def create_email_message(
    to: str,
    subject: str,
    body: str,
    attachment_path: str = ""
):

    # -----------------------------------------------------
    # No attachment
    # -----------------------------------------------------

    if not attachment_path:

        message = MIMEText(
            body,
            "plain",
            "utf-8"
        )

        message["To"] = to
        message["Subject"] = subject

        return message

    # -----------------------------------------------------
    # Attachment exists
    # -----------------------------------------------------

    if not os.path.exists(
        attachment_path
    ):

        raise FileNotFoundError(
            f"Attachment not found: "
            f"{attachment_path}"
        )

    # -----------------------------------------------------
    # Multipart email
    # -----------------------------------------------------

    message = MIMEMultipart()

    message["To"] = to
    message["Subject"] = subject

    # -----------------------------------------------------
    # Add body
    # -----------------------------------------------------

    message.attach(
        MIMEText(
            body,
            "plain",
            "utf-8"
        )
    )

    # -----------------------------------------------------
    # Read file
    # -----------------------------------------------------

    filename = os.path.basename(
        attachment_path
    )

    mime_type, encoding = mimetypes.guess_type(
        attachment_path
    )

    if mime_type:

        main_type, sub_type = mime_type.split(
            "/",
            1
        )

    else:

        main_type = "application"
        sub_type = "octet-stream"

    with open(
        attachment_path,
        "rb"
    ) as file:

        file_data = file.read()

    attachment = MIMEBase(
        main_type,
        sub_type
    )

    attachment.set_payload(
        file_data
    )

    encoders.encode_base64(
        attachment
    )

    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=filename
    )

    message.attach(
        attachment
    )

    return message


# =========================================================
# SEND EMAIL
# =========================================================

@tool
def send_email(
    to: str,
    subject: str,
    body: str,
    attachment_path: str = ""
):
    """
    Send an email through Gmail.

    attachment_path is optional.
    """

    try:

        service = get_gmail_service()

        message = create_email_message(
            to=to,
            subject=subject,
            body=body,
            attachment_path=attachment_path
        )

        encoded_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        result = service.users().messages().send(
            userId="me",
            body={
                "raw": encoded_message
            }
        ).execute()

        if attachment_path:

            return (
                "Email sent successfully "
                "with attachment.\n"
                f"Message ID: {result.get('id')}"
            )

        return (
            "Email sent successfully.\n"
            f"Message ID: {result.get('id')}"
        )

    except Exception as e:

        return (
            f"Failed to send email: {e}"
        )


# =========================================================
# REPLY EMAIL
# =========================================================

@tool
def reply_email(
    message_id: str,
    body: str,
    attachment_path: str = ""
):
    """
    Reply to an existing Gmail message.

    attachment_path is optional.
    """

    if not message_id or not message_id.strip():

        return "Email reply failed: message ID cannot be empty."

    try:

        service = get_gmail_service()

        # -------------------------------------------------
        # Get original email
        # -------------------------------------------------

        original = service.users().messages().get(
            userId="me",
            id=message_id.strip(),
            format="metadata",
            metadataHeaders=[
                "From",
                "To",
                "Subject",
                "Message-ID"
            ]
        ).execute()

        payload = original.get(
            "payload",
            {}
        )

        headers = payload.get(
            "headers",
            []
        )

        sender = get_header(
            headers,
            "From"
        )

        subject = get_header(
            headers,
            "Subject"
        )

        message_id_header = get_header(
            headers,
            "Message-ID"
        )

        # -------------------------------------------------
        # Reply subject
        # -------------------------------------------------

        if subject.lower().startswith(
            "re:"
        ):

            reply_subject = subject

        else:

            reply_subject = f"Re: {subject}"

        # -------------------------------------------------
        # Create reply
        # -------------------------------------------------

        reply = create_email_message(
            to=sender,
            subject=reply_subject,
            body=body,
            attachment_path=attachment_path
        )

        # -------------------------------------------------
        # Gmail threading headers
        # -------------------------------------------------

        if message_id_header:

            reply["In-Reply-To"] = (
                message_id_header
            )

            reply["References"] = (
                message_id_header
            )

        # -------------------------------------------------
        # Encode
        # -------------------------------------------------

        encoded_message = base64.urlsafe_b64encode(
            reply.as_bytes()
        ).decode()

        # -------------------------------------------------
        # Send threaded reply
        # -------------------------------------------------

        result = service.users().messages().send(
            userId="me",
            body={
                "raw": encoded_message,
                "threadId": original.get(
                    "threadId"
                )
            }
        ).execute()

        if attachment_path:

            return (
                "Reply sent successfully "
                "with attachment.\n"
                f"Message ID: {result.get('id')}"
            )

        return (
            "Reply sent successfully.\n"
            f"Message ID: {result.get('id')}"
        )

    except Exception as e:

        return (
            f"Failed to reply to email: {e}"
        )