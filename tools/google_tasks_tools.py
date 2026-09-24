from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/tasks"
]


# =========================
# GOOGLE TASKS SERVICE
# =========================

def get_tasks_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "tasks",
        "v1",
        credentials=credentials
    )

    return service


# =========================
# LIST TASK LISTS
# =========================

@tool
def list_task_lists():
    """
    List the user's Google Tasks task lists.
    """

    service = get_tasks_service()

    result = service.tasklists().list().execute()

    task_lists = result.get("items", [])

    if not task_lists:
        return "No task lists found."

    return [
        {
            "id": task_list["id"],
            "title": task_list["title"]
        }
        for task_list in task_lists
    ]


# =========================
# LIST TASKS
# =========================

@tool
def list_google_tasks(
    task_list_id: str="@default"
):
    """
    List tasks from a Google Tasks task list.
    """

    service = get_tasks_service()

    result = service.tasks().list(
        tasklist=task_list_id,
        showCompleted=True,
        showHidden=False
    ).execute()

    tasks = result.get("items", [])

    if not tasks:
        return "No tasks found."

    return [
        {
            "id": task["id"],
            "title": task.get("title", ""),
            "status": task.get("status", ""),
            "due": task.get("due"),
            "notes": task.get("notes", "")
        }
        for task in tasks
    ]


# =========================
# CREATE TASK
# =========================

@tool
def create_google_task(
    title: str,
    notes: str = "",
    due: str = "",
    task_list_id: str = "@default"
):
    """
    Create a new Google Task.

    due should be an RFC3339 datetime if provided.
    Example: 2026-09-15T10:00:00+05:30
    """

    service = get_tasks_service()

    body = {
        "title": title
    }

    if notes:
        body["notes"] = notes

    if due:
        body["due"] = due

    task = service.tasks().insert(
        tasklist=task_list_id,
        body=body
    ).execute()

    return {
        "id": task["id"],
        "title": task.get("title", ""),
        "status": task.get("status", ""),
        "due": task.get("due"),
        "url": task.get("webViewLink")
    }


# =========================
# UPDATE TASK
# =========================

@tool
def update_google_task(
    task_id: str,
    title: str = "",
    notes: str = "",
    due: str = "",
    task_list_id: str = "@default"
):
    """
    Update an existing Google Task.
    """

    service = get_tasks_service()

    task = service.tasks().get(
        tasklist=task_list_id,
        task=task_id
    ).execute()

    if title:
        task["title"] = title

    if notes:
        task["notes"] = notes

    if due:
        task["due"] = due

    updated_task = service.tasks().update(
        tasklist=task_list_id,
        task=task_id,
        body=task
    ).execute()

    return {
        "id": updated_task["id"],
        "title": updated_task.get("title", ""),
        "status": updated_task.get("status", ""),
        "due": updated_task.get("due")
    }


# =========================
# COMPLETE TASK
# =========================

@tool
def complete_google_task(
    task_id: str,
    task_list_id: str = "@default"
):
    """
    Mark a Google Task as completed.
    """

    service = get_tasks_service()

    task = service.tasks().get(
        tasklist=task_list_id,
        task=task_id
    ).execute()

    task["status"] = "completed"

    updated_task = service.tasks().update(
        tasklist=task_list_id,
        task=task_id,
        body=task
    ).execute()

    return {
        "id": updated_task["id"],
        "title": updated_task.get("title", ""),
        "status": updated_task.get("status", "")
    }


# =========================
# DELETE TASK
# =========================

@tool
def delete_google_task(
    task_id: str,
    task_list_id: str = "@default"
):
    """
    Delete a Google Task.
    """

    service = get_tasks_service()

    service.tasks().delete(
        tasklist=task_list_id,
        task=task_id
    ).execute()

    return "Task deleted successfully."


# =========================
# EXPORT TOOLS
# =========================

google_tasks_tools = [
    list_task_lists,
    list_google_tasks,
    create_google_task,
    update_google_task,
    complete_google_task,
    delete_google_task,
]