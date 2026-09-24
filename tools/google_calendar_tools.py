import os

from datetime import datetime, timedelta
from google_auth import get_google_credentials
from googleapiclient.discovery import build

from langchain_core.tools import tool


# =========================================================
# GOOGLE CALENDAR CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)




# =========================================================
# GOOGLE CALENDAR PERMISSIONS
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]


# =========================================================
# GOOGLE CALENDAR SERVICE
# =========================================================

def get_calendar_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "calendar",
        "v3",
        credentials=credentials
    )

    return service

# =========================================================
# LIST CALENDARS
# =========================================================

@tool
def list_calendars():
    """
    List the user's Google Calendars.

    Returns calendar IDs and names.
    """

    try:

        service = get_calendar_service()

        result = service.calendarList().list().execute()

        calendars = result.get(
            "items",
            []
        )

        if not calendars:

            return "No calendars found."

        output = []

        for calendar in calendars:

            calendar_id = calendar.get(
                "id",
                ""
            )

            summary = calendar.get(
                "summary",
                ""
            )

            output.append(
                f"ID: {calendar_id}\n"
                f"Name: {summary}"
            )

        return "\n\n".join(output)

    except Exception as e:

        return (
            f"Failed to list calendars: {e}"
        )


# =========================================================
# LIST EVENTS
# =========================================================

@tool
def list_calendar_events(
    start_time: str = "",
    end_time: str = "",
    calendar_id: str = "primary",
    max_results: int = 10
):
    """
    List Google Calendar events.

    start_time and end_time should be ISO 8601
    datetime strings when provided.

    Example:
    2026-09-12T00:00:00+05:30
    """

    try:

        service = get_calendar_service()

        max_results = max(
            1,
            min(
                max_results,
                50
            )
        )

        # -------------------------------------------------
        # Default time range
        # -------------------------------------------------

        if not start_time:

            start = datetime.now().astimezone()

        else:

            start = datetime.fromisoformat(
                start_time
            )

        if not end_time:

            end = start + timedelta(
                days=1
            )

        else:

            end = datetime.fromisoformat(
                end_time
            )

        result = service.events().list(
            calendarId=calendar_id,
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = result.get(
            "items",
            []
        )

        if not events:

            return "No calendar events found."

        output = []

        for event in events:

            event_id = event.get(
                "id",
                ""
            )

            summary = event.get(
                "summary",
                "(No title)"
            )

            start_data = event.get(
                "start",
                {}
            )

            end_data = event.get(
                "end",
                {}
            )

            start_value = (
                start_data.get("dateTime")
                or start_data.get("date")
                or ""
            )

            end_value = (
                end_data.get("dateTime")
                or end_data.get("date")
                or ""
            )

            output.append(
                f"ID: {event_id}\n"
                f"Title: {summary}\n"
                f"Start: {start_value}\n"
                f"End: {end_value}"
            )

        return "\n\n".join(output)

    except Exception as e:

        return (
            f"Failed to list calendar events: {e}"
        )


# =========================================================
# SEARCH EVENTS
# =========================================================

@tool
def search_calendar_events(
    query: str,
    calendar_id: str = "primary",
    max_results: int = 10
):
    """
    Search Google Calendar events by text.
    """

    if not query or not query.strip():

        return (
            "Calendar search failed: "
            "query cannot be empty."
        )

    try:

        service = get_calendar_service()

        max_results = max(
            1,
            min(
                max_results,
                50
            )
        )

        result = service.events().list(
            calendarId=calendar_id,
            q=query.strip(),
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = result.get(
            "items",
            []
        )

        if not events:

            return (
                f"No calendar events found for: {query}"
            )

        output = []

        for event in events:

            event_id = event.get(
                "id",
                ""
            )

            summary = event.get(
                "summary",
                "(No title)"
            )

            start_data = event.get(
                "start",
                {}
            )

            start_value = (
                start_data.get("dateTime")
                or start_data.get("date")
                or ""
            )

            output.append(
                f"ID: {event_id}\n"
                f"Title: {summary}\n"
                f"Start: {start_value}"
            )

        return "\n\n".join(output)

    except Exception as e:

        return (
            f"Failed to search calendar: {e}"
        )


# =========================================================
# CREATE EVENT
# =========================================================

@tool
def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary"
):
    """
    Create a Google Calendar event.

    start_time and end_time must be ISO 8601
    datetime strings.

    Example:
    2026-09-12T15:00:00+05:30
    """

    if not title.strip():

        return "Calendar event creation failed: title is required."

    if not start_time.strip():

        return (
            "Calendar event creation failed: "
            "start time is required."
        )

    if not end_time.strip():

        return (
            "Calendar event creation failed: "
            "end time is required."
        )

    try:

        service = get_calendar_service()

        event = {
            "summary": title.strip(),
            "start": {
                "dateTime": start_time,
            },
            "end": {
                "dateTime": end_time,
            },
        }

        if description.strip():

            event["description"] = description.strip()

        if location.strip():

            event["location"] = location.strip()

        result = service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()

        return (
            "Calendar event created successfully.\n"
            f"Event ID: {result.get('id')}\n"
            f"Title: {result.get('summary')}\n"
            f"Start: {result.get('start', {}).get('dateTime', '')}\n"
            f"End: {result.get('end', {}).get('dateTime', '')}"
        )

    except Exception as e:

        return (
            f"Failed to create calendar event: {e}"
        )


# =========================================================
# UPDATE EVENT
# =========================================================

@tool
def update_calendar_event(
    event_id: str,
    title: str = "",
    start_time: str = "",
    end_time: str = "",
    description: str = "",
    location: str = "",
    calendar_id: str = "primary"
):
    """
    Update an existing Google Calendar event.

    event_id must come from an actual Calendar result.
    Only supplied fields are changed.
    """

    if not event_id.strip():

        return (
            "Calendar update failed: "
            "event ID is required."
        )

    try:

        service = get_calendar_service()

        # -------------------------------------------------
        # Get existing event
        # -------------------------------------------------

        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id.strip()
        ).execute()

        # -------------------------------------------------
        # Update supplied fields
        # -------------------------------------------------

        if title.strip():

            event["summary"] = title.strip()

        if description.strip():

            event["description"] = description.strip()

        if location.strip():

            event["location"] = location.strip()

        if start_time.strip():

            event["start"] = {
                "dateTime": start_time
            }

        if end_time.strip():

            event["end"] = {
                "dateTime": end_time
            }

        # -------------------------------------------------
        # Save changes
        # -------------------------------------------------

        result = service.events().update(
            calendarId=calendar_id,
            eventId=event_id.strip(),
            body=event
        ).execute()

        return (
            "Calendar event updated successfully.\n"
            f"Event ID: {result.get('id')}\n"
            f"Title: {result.get('summary', '')}"
        )

    except Exception as e:

        return (
            f"Failed to update calendar event: {e}"
        )


# =========================================================
# DELETE EVENT
# =========================================================

@tool
def delete_calendar_event(
    event_id: str,
    calendar_id: str = "primary"
):
    """
    Delete a Google Calendar event.

    event_id must come from an actual Calendar result.
    """

    if not event_id.strip():

        return (
            "Calendar deletion failed: "
            "event ID is required."
        )

    try:

        service = get_calendar_service()

        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id.strip()
        ).execute()

        return "Calendar event deleted successfully."

    except Exception as e:

        return (
            f"Failed to delete calendar event: {e}"
        )