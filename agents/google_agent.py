import os
from datetime import datetime

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END

# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# GOOGLE TOOLS
# ============================================================

from tools.gmail_tools import (
    check_emails,
    search_emails,
    read_email,
    list_email_attachments,
    download_email_attachment,
    send_email,
    reply_email,
)

from tools.google_calendar_tools import (
    list_calendars,
    list_calendar_events,
    search_calendar_events,
    create_calendar_event,
    update_calendar_event,
    delete_calendar_event,
)

from tools.google_drive_tools import (
    list_drive_files,
    search_drive_files,
    get_drive_file,
    download_drive_file,
    upload_drive_file,
)

from tools.google_docs_tools import (
    create_google_doc,
    read_google_doc,
    append_to_google_doc,
    insert_text_into_google_doc,
    replace_text_in_google_doc,
    delete_text_from_google_doc,
)

from tools.google_sheets_tools import (
    create_google_sheet,
    read_google_sheet,
    write_google_sheet,
    append_to_google_sheet,
    clear_google_sheet,
)

from tools.google_tasks_tools import (
    list_task_lists,
    list_google_tasks,
    create_google_task,
    update_google_task,
    complete_google_task,
    delete_google_task,
)

from tools.google_people_tools import (
    list_google_contacts,
    search_google_contacts,
    get_google_contact,
)

from tools.google_meet_tools import (
    create_google_meeting,
    get_google_meeting_space,
    end_google_meeting,
)

from tools.google_chat_tools import (
    list_google_chat_spaces,
    get_google_chat_space,
    list_google_chat_messages,
    send_google_chat_message,
    get_google_chat_message,
    update_google_chat_message,
    delete_google_chat_message,
)

from tools.google_drive_activity_tools import (
    get_drive_activity,
    get_file_drive_activity,
)

from tools.google_forms_tools import (
    create_google_form,
    get_google_form,
    list_google_form_responses,
    get_google_form_response,
    add_google_form_question,
)

from tools.google_slides_tools import (
    create_google_presentation,
    read_google_presentation,
    add_google_slide,
    insert_text_into_slide,
    create_text_box_on_slide,
    delete_google_slide,
)

from tools.youtube_tools import (
    search_youtube,
    get_youtube_video,
    get_my_youtube_channel,
    list_my_youtube_videos,
)

from tools.youtube_analytics_tools import (
    get_youtube_channel_analytics,
    get_youtube_video_analytics,
    get_youtube_traffic_sources,
    get_top_youtube_videos,
    get_youtube_subscriber_analytics,
)


# ============================================================
# TOOL GROUPS
# ============================================================

GMAIL_TOOLS = [
    check_emails,
    search_emails,
    read_email,
    list_email_attachments,
    download_email_attachment,
    send_email,
    reply_email,
]

CALENDAR_TOOLS = [
    list_calendars,
    list_calendar_events,
    search_calendar_events,
    create_calendar_event,
    update_calendar_event,
    delete_calendar_event,
]

DRIVE_TOOLS = [
    list_drive_files,
    search_drive_files,
    get_drive_file,
    download_drive_file,
    upload_drive_file,
]

DOCS_TOOLS = [
    create_google_doc,
    read_google_doc,
    append_to_google_doc,
    insert_text_into_google_doc,
    replace_text_in_google_doc,
    delete_text_from_google_doc,
]

SHEETS_TOOLS = [
    create_google_sheet,
    read_google_sheet,
    write_google_sheet,
    append_to_google_sheet,
    clear_google_sheet,
]

TASKS_TOOLS = [
    list_task_lists,
    list_google_tasks,
    create_google_task,
    update_google_task,
    complete_google_task,
    delete_google_task,
]

PEOPLE_TOOLS = [
    list_google_contacts,
    search_google_contacts,
    get_google_contact,
]

MEET_TOOLS = [
    create_google_meeting,
    get_google_meeting_space,
    end_google_meeting,
]

CHAT_TOOLS = [
    list_google_chat_spaces,
    get_google_chat_space,
    list_google_chat_messages,
    send_google_chat_message,
    get_google_chat_message,
    update_google_chat_message,
    delete_google_chat_message,
]

DRIVE_ACTIVITY_TOOLS = [
    get_drive_activity,
    get_file_drive_activity,
]

FORMS_TOOLS = [
    create_google_form,
    get_google_form,
    list_google_form_responses,
    get_google_form_response,
    add_google_form_question,
]

SLIDES_TOOLS = [
    create_google_presentation,
    read_google_presentation,
    add_google_slide,
    insert_text_into_slide,
    create_text_box_on_slide,
    delete_google_slide,
]

YOUTUBE_TOOLS = [
    search_youtube,
    get_youtube_video,
    get_my_youtube_channel,
    list_my_youtube_videos,
]

YOUTUBE_ANALYTICS_TOOLS = [
    get_youtube_channel_analytics,
    get_youtube_video_analytics,
    get_youtube_traffic_sources,
    get_top_youtube_videos,
    get_youtube_subscriber_analytics,
]


# ============================================================
# GOOGLE TOOL GROUP MAP
# ============================================================

GOOGLE_TOOL_GROUPS = {
    "gmail": GMAIL_TOOLS,
    "calendar": CALENDAR_TOOLS,
    "drive": DRIVE_TOOLS,
    "docs": DOCS_TOOLS,
    "sheets": SHEETS_TOOLS,
    "tasks": TASKS_TOOLS,
    "people": PEOPLE_TOOLS,
    "meet": MEET_TOOLS,
    "chat": CHAT_TOOLS,
    "drive_activity": DRIVE_ACTIVITY_TOOLS,
    "forms": FORMS_TOOLS,
    "slides": SLIDES_TOOLS,
    "youtube": YOUTUBE_TOOLS,
    "youtube_analytics": YOUTUBE_ANALYTICS_TOOLS,
}


# ============================================================
# GOOGLE SERVICE ROUTER
# ============================================================

GOOGLE_ROUTER_PROMPT = """
You are the Google Service Router for a desktop AI agent.

Determine which Google service is required for the user's request.

Available services:

- gmail
- calendar
- drive
- docs
- sheets
- tasks
- people
- meet
- chat
- drive_activity
- forms
- slides
- youtube
- youtube_analytics

Return ONLY the service name.

Examples:

"check my emails" -> gmail
"send an email" -> gmail
"what meetings do I have tomorrow" -> calendar
"create a calendar event" -> calendar
"find a file in my Google Drive" -> drive
"create a Google document" -> docs
"update my spreadsheet" -> sheets
"create a task" -> tasks
"find my contacts" -> people
"create a Google Meet" -> meet
"send a Google Chat message" -> chat
"who modified this Drive file" -> drive_activity
"create a Google Form" -> forms
"create a presentation" -> slides
"search YouTube" -> youtube
"show my YouTube analytics" -> youtube_analytics
"""


# ============================================================
# LLM
# ============================================================

llm = ChatOpenAI(
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    model="deepseek-v4-flash",
    tiktoken_model_name="gpt-4o-mini",
)


# ============================================================
# STATE
# ============================================================

class GoogleAgentState(MessagesState):
    selected_group: str


# ============================================================
# ROUTER NODE
# ============================================================

def google_router(state: GoogleAgentState):
    """
    Decide which Google service should handle the request.
    """

    messages = state["messages"]

    now = datetime.now().astimezone()

    current_context = f"""
Current date: {now.strftime("%Y-%m-%d")}
Current time: {now.strftime("%H:%M")}
Day: {now.strftime("%A")}
"""

    response = llm.invoke([
        {
            "role": "system",
            "content": GOOGLE_ROUTER_PROMPT + "\n" + current_context,
        },
        {
            "role": "user",
            "content": messages[-1].content,
        },
    ])

    selected_group = response.content.strip().lower()

    if selected_group not in GOOGLE_TOOL_GROUPS:
        selected_group = "gmail"

    return {
        "selected_group": selected_group
    }

# ============================================================
# SERVICE AGENT
# ============================================================

def google_service_agent(state: GoogleAgentState):
    """
    Bind only the tools belonging to the selected Google service.
    """

    selected_group = state.get("selected_group")

    tools = GOOGLE_TOOL_GROUPS.get(selected_group, [])

    if not tools:
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": "I could not determine the required Google service."
                }
            ]
        }

    now = datetime.now().astimezone()

    system_message = {
        "role": "system",
        "content": f"""
You are the {selected_group} Google service agent.

Current date: {now.strftime("%Y-%m-%d")}
Current time: {now.strftime("%H:%M")}
Today is: {now.strftime("%A")}

Never guess the current date.
Interpret words such as:
- today
- tomorrow
- yesterday
- this week
- next week

relative to the current date above.

Use the available tools to fulfill the user's request.
Do not claim a tool action succeeded unless the tool actually succeeds.
""",
    }

    service_llm = llm.bind_tools(tools)

    response = service_llm.invoke(
        [system_message] + state["messages"]
    )

    return {
        "messages": [response]
    }

# ============================================================
# TOOL ROUTER
# ============================================================

def route_after_service_agent(state: GoogleAgentState):
    """
    If the service agent requested a tool, execute it.
    Otherwise finish.
    """

    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END


# ============================================================
# DYNAMIC TOOL NODE
# ============================================================

def google_tools_node(state: GoogleAgentState):
    """
    Execute only the tools belonging to the selected group.
    """

    selected_group = state.get("selected_group")

    tools = GOOGLE_TOOL_GROUPS.get(selected_group, [])

    if not tools:
        return {}

    tool_node = ToolNode(tools)

    return tool_node.invoke(state)


# ============================================================
# BUILD GOOGLE GRAPH
# ============================================================

google_graph_builder = StateGraph(GoogleAgentState)

google_graph_builder.add_node(
    "google_router",
    google_router
)

google_graph_builder.add_node(
    "google_service_agent",
    google_service_agent
)

google_graph_builder.add_node(
    "tools",
    google_tools_node
)

google_graph_builder.add_edge(
    START,
    "google_router"
)

google_graph_builder.add_edge(
    "google_router",
    "google_service_agent"
)

google_graph_builder.add_conditional_edges(
    "google_service_agent",
    route_after_service_agent,
    {
        "tools": "tools",
        END: END,
    }
)

google_graph_builder.add_edge(
    "tools",
    "google_service_agent"
)

google_graph = google_graph_builder.compile()


# ============================================================
# RUN GOOGLE AGENT
# ============================================================

def run_google_agent(user_input: str):
    """
    Run the Google Agent with a user request.
    """

    result = google_graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_input,
                }
            ]
        }
    )

    return result["messages"][-1].content


# ============================================================
# EXPORT
# ============================================================

google_tools = []

for group_tools in GOOGLE_TOOL_GROUPS.values():
    google_tools.extend(group_tools)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("Google Agent")
    print("=" * 50)

    print("Google service groups:")
    for group, group_tools in GOOGLE_TOOL_GROUPS.items():
        print(f"{group}: {len(group_tools)} tools")

    print("=" * 50)
    print(f"Total Google tools: {len(google_tools)}")

    while True:

        user_input = input("\nYou: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            break

        try:
            response = run_google_agent(user_input)
            print("\nAgent:", response)

        except Exception as e:
            print("\nError:", e)