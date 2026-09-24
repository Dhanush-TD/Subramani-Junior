from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/drive.activity.readonly"
]


# =========================
# GOOGLE DRIVE ACTIVITY SERVICE
# =========================

def get_drive_activity_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "driveactivity",
        "v2",
        credentials=credentials
    )

    return service


# =========================
# QUERY DRIVE ACTIVITY
# =========================

@tool
def get_drive_activity(
    page_size: int = 20
):
    """
    Get recent activity in the user's Google Drive.
    """

    service = get_drive_activity_service()

    page_size = min(max(page_size, 1), 100)

    response = service.activity().query(
        body={
            "pageSize": page_size,
            "consolidationStrategy": {
                "none": {}
            }
        }
    ).execute()

    activities = response.get("activities", [])

    if not activities:
        return "No recent Drive activity found."

    results = []

    for activity in activities:

        timestamp = activity.get("timestamp", "")

        time_range = activity.get("timeRange", {})

        actions = activity.get("actions", [])

        targets = activity.get("targets", [])

        actors = activity.get("actors", [])

        action_types = []

        for action in actions:

            action_detail = action.get("detail", {})

            action_type = next(
                (
                    key
                    for key, value in action_detail.items()
                    if value
                ),
                "unknown"
            )

            action_types.append(action_type)

        target_info = []

        for target in targets:

            drive_item = target.get("driveItem", {})

            target_info.append({
                "name": drive_item.get("title", ""),
                "mime_type": drive_item.get("mimeType", ""),
                "drive_item_name": drive_item.get("name", "")
            })

        actor_info = []

        for actor in actors:

            user = actor.get("user", {})

            known_user = user.get("knownUser", {})

            actor_info.append({
                "display_name": known_user.get(
                    "personName",
                    ""
                )
            })

        results.append({
            "timestamp": timestamp,
            "time_range": time_range,
            "actions": action_types,
            "targets": target_info,
            "actors": actor_info
        })

    return results


# =========================
# QUERY ACTIVITY FOR A FILE
# =========================

@tool
def get_file_drive_activity(
    file_name: str,
    page_size: int = 20
):
    """
    Get Drive activity for a specific file or Drive item.

    file_name should be the Drive item resource name,
    for example:

    items/123456789
    """

    service = get_drive_activity_service()

    page_size = min(max(page_size, 1), 100)

    response = service.activity().query(
        body={
            "pageSize": page_size,
            "itemName": file_name,
            "consolidationStrategy": {
                "none": {}
            }
        }
    ).execute()

    activities = response.get("activities", [])

    if not activities:
        return "No activity found for this Drive item."

    return activities


# =========================
# EXPORT TOOLS
# =========================

google_drive_activity_tools = [
    get_drive_activity,
    get_file_drive_activity,
]