from langchain_core.tools import tool

from agents.google_agent import run_google_agent


@tool
def google_agent(user_request: str):
    """
    Handle Google-related requests using the dedicated Google Agent.

    Use this for Gmail, Calendar, Drive, Docs, Sheets, Tasks,
    Contacts, Meet, Chat, Forms, Slides, YouTube, and YouTube Analytics.
    """
    return run_google_agent(user_request)