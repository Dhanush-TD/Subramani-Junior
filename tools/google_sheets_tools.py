import os

from google_auth import get_google_credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool


# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


# =========================
# GOOGLE SHEETS SERVICE
# =========================

def get_sheets_service():

    credentials = get_google_credentials(
        SCOPES
    )

    service = build(
        "sheets",
        "v4",
        credentials=credentials
    )

    return service


# =========================
# CREATE SPREADSHEET
# =========================

@tool
def create_google_sheet(title: str):
    """
    Create a new Google Spreadsheet.
    """

    service = get_sheets_service()

    spreadsheet = service.spreadsheets().create(
        body={
            "properties": {
                "title": title
            }
        }
    ).execute()

    spreadsheet_id = spreadsheet["spreadsheetId"]

    return {
        "spreadsheet_id": spreadsheet_id,
        "title": spreadsheet["properties"]["title"],
        "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    }


# =========================
# READ SHEET DATA
# =========================

@tool
def read_google_sheet(
    spreadsheet_id: str,
    range_name: str
):
    """
    Read data from a Google Spreadsheet range.

    Example range:
    Sheet1!A1:D10
    """

    service = get_sheets_service()

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get("values", [])

    if not values:
        return "No data found."

    return values


# =========================
# WRITE SHEET DATA
# =========================

@tool
def write_google_sheet(
    spreadsheet_id: str,
    range_name: str,
    values: list
):
    """
    Write data to a Google Spreadsheet.

    values should be a 2D list.

    Example:
    [["Name", "Age"], ["Dhanush", 22]]
    """

    service = get_sheets_service()

    body = {
        "values": values
    }

    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

    return {
        "updated_range": result.get("updatedRange"),
        "updated_rows": result.get("updatedRows"),
        "updated_columns": result.get("updatedColumns"),
        "updated_cells": result.get("updatedCells")
    }


# =========================
# APPEND DATA
# =========================

@tool
def append_to_google_sheet(
    spreadsheet_id: str,
    range_name: str,
    values: list
):
    """
    Append rows to a Google Spreadsheet.

    values should be a 2D list.
    """

    service = get_sheets_service()

    body = {
        "values": values
    }

    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

    return {
        "updated_range": result.get("updates", {}).get("updatedRange"),
        "updated_rows": result.get("updates", {}).get("updatedRows"),
        "updated_columns": result.get("updates", {}).get("updatedColumns"),
        "updated_cells": result.get("updates", {}).get("updatedCells")
    }


# =========================
# CLEAR SHEET DATA
# =========================

@tool
def clear_google_sheet(
    spreadsheet_id: str,
    range_name: str
):
    """
    Clear values from a Google Spreadsheet range.
    """

    service = get_sheets_service()

    result = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        body={}
    ).execute()

    return {
        "cleared_range": result.get("clearedRange")
    }


# =========================
# EXPORT TOOLS
# =========================

google_sheets_tools = [
    create_google_sheet,
    read_google_sheet,
    write_google_sheet,
    append_to_google_sheet,
    clear_google_sheet,
]