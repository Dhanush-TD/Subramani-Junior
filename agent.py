import os
import asyncio
import subprocess
import atexit
import socket
import time
import json
from datetime import datetime

from dotenv import load_dotenv

from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.messages import trim_messages

from langgraph.graph import (
    StateGraph,
    MessagesState,
    START,
    END,
)
from langgraph.prebuilt import ToolNode, tools_condition


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()
load_dotenv(r"D:\local-file-agent\whatsapp_mcp\.env", override=True)


# ============================================================
# LLM
# ============================================================

llm = ChatOpenAI(
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    model="deepseek-flash",
    tiktoken_model_name="gpt-4o-mini",
)


# ============================================================
# RAG
# ============================================================



from tools.rag_agent_tools import (
    search_file_by_content,
)

from tools.screen_context_tools import (
    prepare_screen_context,
)

# ============================================================
# WHATSAPP MCP
# ============================================================

from langchain_mcp_adapters.client import MultiServerMCPClient


# ============================================================
# WHATSAPP BRIDGE
# ============================================================

WHATSAPP_BRIDGE_PATH = (
    r"D:\local-file-agent\whatsapp_mcp"
    r"\whatsapp-bridge\whatsapp-client.exe"
)

whatsapp_bridge_process = None


def start_whatsapp_bridge():

    global whatsapp_bridge_process

    if whatsapp_bridge_process is not None:

        if whatsapp_bridge_process.poll() is None:
            return

    print("[WhatsApp] Starting bridge...")

    bridge_dir = os.path.dirname(
        WHATSAPP_BRIDGE_PATH
    )

    whatsapp_bridge_process = subprocess.Popen(
        [WHATSAPP_BRIDGE_PATH],
        cwd=bridge_dir,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    print("[WhatsApp] Bridge started.")


def wait_for_whatsapp_bridge(timeout=100):

    print("[WhatsApp] Waiting for bridge API...")

    start_time = time.time()

    while time.time() - start_time < timeout:

        # ----------------------------------------------------
        # Check process
        # ----------------------------------------------------

        if whatsapp_bridge_process is not None:

            return_code = whatsapp_bridge_process.poll()

            if return_code is not None:

                print(
                    f"[WhatsApp] Bridge exited with code "
                    f"{return_code}."
                )

                return False

        # ----------------------------------------------------
        # Check API
        # ----------------------------------------------------

        try:

            with socket.create_connection(
                ("127.0.0.1", 8080),
                timeout=1,
            ):

                print(
                    "[WhatsApp] Bridge API is ready."
                )

                return True

        except (ConnectionRefusedError, OSError):

            time.sleep(0.5)

    print(
        "[WhatsApp] Bridge API did not become ready."
    )

    return False


def stop_whatsapp_bridge():

    global whatsapp_bridge_process

    if whatsapp_bridge_process is None:
        return

    if whatsapp_bridge_process.poll() is None:

        print(
            "\n[WhatsApp] Stopping bridge..."
        )

        whatsapp_bridge_process.terminate()

        try:

            whatsapp_bridge_process.wait(
                timeout=5
            )

        except subprocess.TimeoutExpired:

            whatsapp_bridge_process.kill()

        print(
            "[WhatsApp] Bridge stopped."
        )

    whatsapp_bridge_process = None


atexit.register(
    stop_whatsapp_bridge
)


start_whatsapp_bridge()
wait_for_whatsapp_bridge()


# ============================================================
# WHATSAPP MCP CLIENT
# ============================================================

WHATSAPP_MCP_CLIENT = MultiServerMCPClient(
    {
        "whatsapp": {

            "command": "uv",

            "args": [
                "run",
                "python",
                "main.py",
            ],

            "cwd": (
                r"D:\local-file-agent\whatsapp_mcp"
                r"\whatsapp-mcp-server"
            ),

            "transport": "stdio",
        }
    }
)


async def load_whatsapp_mcp_tools():

    return await (
        WHATSAPP_MCP_CLIENT.get_tools()
    )


WHATSAPP_MCP_TOOLS = asyncio.run(
    load_whatsapp_mcp_tools()
)


def make_sync_mcp_tool(mcp_tool):

    def sync_tool(**kwargs):

        return asyncio.run(
            mcp_tool.ainvoke(kwargs)
        )

    sync_tool.__name__ = mcp_tool.name

    sync_tool.__doc__ = (
        mcp_tool.description
    )

    return StructuredTool.from_function(
        func=sync_tool,
        name=mcp_tool.name,
        description=mcp_tool.description,
        args_schema=mcp_tool.args_schema,
    )


WHATSAPP_TOOLS = [
    make_sync_mcp_tool(tool)
    for tool in WHATSAPP_MCP_TOOLS
]


# ============================================================
# MEMORY
# ============================================================

from memory.session_memory import (
    SessionMemory,
)

from memory.long_term_memory import (
    LongTermMemory,
)

from tools.memory_tools import (
    save_memory,
    search_long_term_memory,
    get_all_memories,
)


# ============================================================
# LOCAL SYSTEM TOOLS
# ============================================================

from tools.bluetooth_tools import (
    get_bluetooth_status,
    turn_bluetooth_on,
    turn_bluetooth_off,
)

from tools.browser_tools import (
    browser_task,
)

from tools.web_tools import (
    web_search,
)

from tools.screenshot_tools import (
    take_screenshot,
)

from tools.coding_tools import (
    coding_tool,
)

from tools.brightness_tools import (
    get_brightness,
    set_brightness,
    increase_brightness,
    decrease_brightness,
)

from tools.system_tools import (
    get_volume,
    set_volume,
    increase_volume,
    decrease_volume,
    mute_volume,
    unmute_volume,
)

from tools.file_tools import (
    search_file,
    get_file,
    read_file,
    open_file,
    write_file,
    move_file,
    copy_file,
)

from tools.folder_tools import (
    search_folder,
    open_folder,
    move_folder,
    copy_folder,
)

from tools.application_tools import (
    open_application,
    close_application,
    open_file_with_application,
    open_folder_with_application,
    find_application_path,
)

from tools.messaging_tools import (
    send_message,
    send_file,
)

from tools.network_tools import (
    get_wifi_status,
    turn_wifi_on,
    turn_wifi_off,
)

from tools.terminal_tool import (
    terminal_tool,
)


# ============================================================
# GOOGLE TOOLS
# ============================================================

# ------------------------------------------------------------
# Gmail
# ------------------------------------------------------------

from tools.gmail_tools import (
    check_emails,
    search_emails,
    read_email,
    list_email_attachments,
    download_email_attachment,
    send_email,
    reply_email,
)


# ------------------------------------------------------------
# Calendar
# ------------------------------------------------------------

from tools.google_calendar_tools import (
    list_calendars,
    list_calendar_events,
    search_calendar_events,
    create_calendar_event,
    update_calendar_event,
    delete_calendar_event,
)


# ------------------------------------------------------------
# Drive
# ------------------------------------------------------------

from tools.google_drive_tools import (
    list_drive_files,
    search_drive_files,
    get_drive_file,
    download_drive_file,
    upload_drive_file,
)


# ------------------------------------------------------------
# Docs
# ------------------------------------------------------------

from tools.google_docs_tools import (
    create_google_doc,
    read_google_doc,
    append_to_google_doc,
    insert_text_into_google_doc,
    replace_text_in_google_doc,
    delete_text_from_google_doc,
)


# ------------------------------------------------------------
# Sheets
# ------------------------------------------------------------

from tools.google_sheets_tools import (
    create_google_sheet,
    read_google_sheet,
    write_google_sheet,
    append_to_google_sheet,
    clear_google_sheet,
)


# ------------------------------------------------------------
# Tasks
# ------------------------------------------------------------

from tools.google_tasks_tools import (
    list_task_lists,
    list_google_tasks,
    create_google_task,
    update_google_task,
    complete_google_task,
    delete_google_task,
)


# ------------------------------------------------------------
# People
# ------------------------------------------------------------

from tools.google_people_tools import (
    list_google_contacts,
    search_google_contacts,
    get_google_contact,
)


# ------------------------------------------------------------
# Meet
# ------------------------------------------------------------

from tools.google_meet_tools import (
    create_google_meeting,
    end_google_meeting,
    get_google_meeting_space,
)


# ------------------------------------------------------------
# Google Chat
# ------------------------------------------------------------

from tools.google_chat_tools import (
    list_google_chat_spaces,
    get_google_chat_space,
    list_google_chat_messages,
    send_google_chat_message,
    get_google_chat_message,
    update_google_chat_message,
    delete_google_chat_message,
)


# ------------------------------------------------------------
# Drive Activity
# ------------------------------------------------------------

from tools.google_drive_activity_tools import (
    get_drive_activity,
    get_file_drive_activity,
)


# ------------------------------------------------------------
# Forms
# ------------------------------------------------------------

from tools.google_forms_tools import (
    create_google_form,
    get_google_form,
    list_google_form_responses,
    get_google_form_response,
    add_google_form_question,
)


# ------------------------------------------------------------
# Slides
# ------------------------------------------------------------

from tools.google_slides_tools import (
    create_google_presentation,
    read_google_presentation,
    add_google_slide,
    insert_text_into_slide,
    create_text_box_on_slide,
    delete_google_slide,
)


# ------------------------------------------------------------
# YouTube
# ------------------------------------------------------------

from tools.youtube_tools import (
    search_youtube,
    get_youtube_video,
    get_my_youtube_channel,
    list_my_youtube_videos,
)


# ------------------------------------------------------------
# YouTube Analytics
# ------------------------------------------------------------

from tools.youtube_analytics_tools import (
    get_youtube_channel_analytics,
    get_youtube_video_analytics,
    get_youtube_traffic_sources,
    get_top_youtube_videos,
    get_youtube_subscriber_analytics,
)


# ============================================================
# MEMORY INSTANCES
# ============================================================

# Long-term memory is intentionally shared across conversations.
# It represents user-level memories that should persist across chats.
long_term_memory = LongTermMemory()


# Session memory is isolated per conversation.
# conversation_id -> SessionMemory instance
session_memories = {}


def get_session_memory(conversation_id):
    """Return the session memory belonging to one conversation."""

    if conversation_id not in session_memories:
        session_memories[conversation_id] = SessionMemory()

    return session_memories[conversation_id]


# ============================================================
# TOOL GROUPS
# ============================================================

FILE_TOOLS = [
    search_file,
    get_file,
    read_file,
    open_file,
    write_file,
    move_file,
    copy_file,
    open_file_with_application,
]


RAG_TOOLS = [
    search_file_by_content,
]


FOLDER_TOOLS = [
    search_folder,
    open_folder,
    move_folder,
    copy_folder,
    open_folder_with_application,
]


APPLICATION_TOOLS = [
    open_application,
    close_application,
    find_application_path,
    open_file_with_application,
    open_folder_with_application,
]


MESSAGING_TOOLS = [
    send_message,
    send_file,
]


VOLUME_TOOLS = [
    get_volume,
    set_volume,
    increase_volume,
    decrease_volume,
    mute_volume,
    unmute_volume,
]


BRIGHTNESS_TOOLS = [
    get_brightness,
    set_brightness,
    increase_brightness,
    decrease_brightness,
]


BLUETOOTH_TOOLS = [
    get_bluetooth_status,
    turn_bluetooth_on,
    turn_bluetooth_off,
]


WIFI_TOOLS = [
    get_wifi_status,
    turn_wifi_on,
    turn_wifi_off,
]


SCREENSHOT_TOOLS = [
    take_screenshot,
]


WEB_TOOLS = [
    web_search,
]


BROWSER_TOOLS = [
    browser_task,
]


TERMINAL_TOOLS = [
    terminal_tool,
]


MEMORY_TOOLS = [
    save_memory,
    search_long_term_memory,
    get_all_memories,
]


# ============================================================
# GOOGLE TOOL GROUPS
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

CODING_TOOLS = [
    coding_tool,
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
# ALL TOOL GROUPS
# ============================================================

TOOL_GROUPS = {

    # Local
    "file": FILE_TOOLS,
    "rag": RAG_TOOLS,
    "folder": FOLDER_TOOLS,
    "application": APPLICATION_TOOLS,
    "messaging": MESSAGING_TOOLS,
    "volume": VOLUME_TOOLS,
    "brightness": BRIGHTNESS_TOOLS,
    "bluetooth": BLUETOOTH_TOOLS,
    "wifi": WIFI_TOOLS,
    "screenshot": SCREENSHOT_TOOLS,
    "web": WEB_TOOLS,
    "browser": BROWSER_TOOLS,
    "terminal": TERMINAL_TOOLS,
    "whatsapp": WHATSAPP_TOOLS,
    "memory": MEMORY_TOOLS,
    "coding": CODING_TOOLS,

    # Google
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
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """

You are a local Windows AI desktop assistant.

You have access to grouped tools.


============================================================
GENERAL
============================================================

1. Understand the user's request using the conversation context.

2. If the request requires no tool, answer directly.

3. If the request requires a tool, select the group or groups
   required to complete the CURRENT ACTION.

4. Never claim an action succeeded unless the actual tool
   succeeds.

5. Never invent identifiers, filenames, paths, phone numbers,
   JIDs, message IDs, event IDs, email IDs, document IDs,
   spreadsheet IDs, task IDs, contact IDs, or other identifiers.

6. If a tool returns an error, report the failure clearly.

7. Keep final responses concise.


============================================================
FILE RETURN RULES: "SHOW" / "GIVE" VS "OPEN" (CRITICAL)
============================================================

1. IF THE USER SAYS "SHOW" OR "GIVE" (e.g. "show me the file", "give me good.txt", "show the screenshot", "show it to me"):
   - You must RETURN THE FILE DIRECTLY IN THE CHAT AS AN ATTACHMENT / FILE CARD.
   - For image files (PNG, JPG, JPEG, GIF, WEBP, SVG):
     Render the image directly in the chat using Markdown image syntax:
     ![Image Name](C:/path/to/image.png)
     (The chat UI automatically renders this as an inline interactive image card).
   - For all other files (text files, code, documents, PDF, spreadsheets, archives, etc.):
     Return the file directly using Markdown file attachment link syntax:
     [filename.ext](C:/path/to/file.ext)
     Example: [good.txt](C:/Users/dhanu/Downloads/hi/hiii/yeee/good.txt)
     (The desktop UI automatically renders this as a rich, interactive file attachment card with Open and Download buttons, exactly like Claude).
   - DO NOT dump the file content or code into code blocks unless the user explicitly asks to "read", "print", "display contents", or "what is written inside".
   - DO NOT write "Contents: ..." or "Path: `C:\...`" in code blocks. Simply provide the file card link [filename](filepath).
   - NEVER call open_file, open_application, or open_file_with_application when the user says "show", "give", "display", "get", or "view".
   - Do NOT launch or open any external application window on the Windows desktop for "show" or "give".

2. ONLY OPEN ON THE OPERATING SYSTEM IF THE USER EXPLICITLY SAYS "OPEN":
   - ONLY call open_file, open_application, or open_file_with_application (launching an app/window on the desktop) if the user's message EXPLICITLY contains the word "open" (e.g. "open good.txt", "open Notepad", "open this in VS Code").
   - If the user did NOT explicitly say "open", NEVER launch an application or open the file on the operating system.


============================================================
IMAGE & MEDIA DISPLAY RULES
============================================================

1. The desktop application UI AUTOMATICALLY renders inline image cards for any local image file path.
2. Whenever you take a screenshot, capture the screen, create an image, reference a local image file, or the user asks to "show" or "give" an image, ALWAYS include the full image path in your final response using standard Markdown image syntax:
   ![Screenshot](C:/Users/dhanu/Desktop/Screenshot_filename.png)
3. NEVER state "I cannot display images inline" or "the image is saved to disk so I can't show it here". The chat UI automatically renders the image inline to the user when you include the Markdown image tag `![Screenshot](filepath)`.


============================================================
VERY IMPORTANT: FOLLOW-UP CONTEXT
============================================================

The conversation history is authoritative.

The latest user message is NOT always a new task.

A short message may be an answer to a clarification from the
previous assistant message.

When this happens, continue the EXISTING task.

Example:

User:
send hello to Sam on WhatsApp

Assistant:
Which Sam?

User:
Sam AIDS

"Sam AIDS" is NOT a new unrelated request.

It is the answer to the previous clarification.

Continue the previous WhatsApp task.


============================================================
RESOLVED INFORMATION MUST BE REUSED
============================================================

When information has already been resolved earlier in the
conversation, REUSE it.

Do NOT search for or rediscover information that is already
known.

Resolved information can include:

- file paths
- filenames
- folder paths
- selected folders
- selected contacts
- phone numbers
- JIDs
- email addresses
- selected emails
- event IDs
- task IDs
- document IDs
- spreadsheet IDs
- application paths
- message IDs
- any other identifiers


Example:

User:
find good.txt

Assistant:
I found:

1. C:\\Users\\dhanu\\Downloads\\hi\\good.txt
2. C:\\Users\\dhanu\\Downloads\\hi\\hiii\\yeee\\good.txt

Assistant:
Which one?

User:
the one in yeee folder

The second file is now RESOLVED.

Its exact path is:

C:\\Users\\dhanu\\Downloads\\hi\\hiii\\yeee\\good.txt

If the user later says:

send it to Gowtham on WhatsApp

DO NOT search for good.txt again.

Reuse the already resolved path.


============================================================
REMAINING ACTION DETERMINES TOOL GROUP
============================================================

Select tool groups based on what action STILL NEEDS to be
performed.

Do NOT select a group merely because an object from that group
appeared earlier in the conversation.

If an object has already been resolved, its group does not need
to be selected again just to rediscover that object.


Example:

Previous task:

send good.txt from the yeee folder to Gowtham on WhatsApp

File is already resolved:

C:\\Users\\dhanu\\Downloads\\hi\\hiii\\yeee\\good.txt

Assistant:
Which Gowtham?

User:
Gowtham AIDS

At this point:

File = already resolved

Recipient = now resolved

Remaining action = send the file using WhatsApp

Required group:

whatsapp

Do NOT select:

file + whatsapp

Do NOT search for good.txt again.

Do NOT use RAG.

Use the previously resolved file path.


============================================================
MULTI-STEP TASKS
============================================================

A task may require several user turns.

Example:

User:
send good.txt from the yeee folder to Gowtham on WhatsApp

Assistant:
Which Gowtham?

User:
Gowtham AIDS

The final message completes the previous task.

The complete task is:

Action:
send file

File:
C:\\Users\\dhanu\\Downloads\\hi\\hiii\\yeee\\good.txt

Recipient:
Gowtham AIDS

Channel:
WhatsApp

Continue and execute the task.

Do NOT restart the task.

Do NOT search for the file again.

Do NOT ask for information already resolved.


============================================================
CLARIFICATION ANSWERS
============================================================

If the previous assistant asked a question, determine exactly
what information that question requested.

If the user provides that information, treat it as the answer
to that question.

Examples:

"Sam AIDS"
"number 2"
"the second file"
"the yeee folder one"
"yes"
"that one"
"tomorrow"
"send it"
"do that"

Use the previous conversation to determine what these refer to.

Do NOT interpret a clarification answer as a new unrelated task.


============================================================
DO NOT REDISCOVER RESOLVED INFORMATION
============================================================

Before requesting a tool group, check the conversation context.

If the required value already exists in the conversation,
reuse it.

Do not:

- search for an already selected file
- search for an already selected folder
- search for an already selected contact
- search for an already selected email
- search for an already selected event
- search for an already selected application

unless:

1. the user explicitly asks to search again, OR
2. the previous information is genuinely insufficient.


============================================================
WHATSAPP
============================================================

Use WhatsApp MCP tools for WhatsApp operations.

When the user gives a contact name:

1. Search contacts if necessary.

2. If multiple contacts are returned, ask the user to choose.

3. The next short user reply may be the contact selection.

4. Treat that reply as part of the previous WhatsApp task.

5. Use the exact identifier returned by WhatsApp.

6. Never invent phone numbers, JIDs, chat IDs or message IDs.

If the user says:

"Sam AIDS"

after being asked which Sam to message, interpret it as:

"Use the Sam AIDS contact for the previous WhatsApp task."

Do NOT ask whether this is about WhatsApp again.

Never claim a message or file was sent unless the WhatsApp
send tool succeeds.


============================================================
FILES
============================================================

Use file tools for local files.

SHOW / GIVE VS OPEN:
- "show" or "give" (e.g. "show me good.txt", "give me the file"): Return the file directly in the chat window.
  - Image files: return inline image markdown ![Image](path).
  - Text / code / document files: read and display content inside chat using read_file, or provide the file path/content.
  - NEVER launch an external desktop application or call open_file for "show" or "give".
- "open": ONLY launch/open a file on the Windows desktop if the user explicitly uses the word "open" in their message.

FILE SEARCH VS CONTENT SEARCH:

There are two different types of file search.

1. FILE LOCATION SEARCH:

When the user wants to find or locate a file by:

- filename
- partial filename
- file extension
- file path
- filename pattern

use the normal file search tools.

Examples:

"Find code_test.py"
"Find all .txt files"
"Locate my resume.pdf"
"Search for files named good.txt"

These are FILE LOCATION requests.

Do NOT use RAG/search_file_by_content for these requests.

2. FILE CONTENT SEARCH:

Use RAG/search_file_by_content only when the user wants to
search INSIDE files or find information contained in files.

Examples:

"Find the file that contains information about LangGraph"
"What does my resume say about Python?"
"Search my documents for the word LangChain"
"Find information about WhatsApp media roots inside my files"

These are FILE CONTENT requests.

IMPORTANT:

Filename/path search = normal file tools.

Folder-name/path search = normal folder tools.

Content/information inside files = RAG.

Never use RAG merely to locate a file or folder by name.

If a file path has already been resolved, reuse that exact path.

Do not perform another RAG search merely because the user says
"it", "that file", "the selected file", "the second one", etc.


============================================================
FOLDERS
============================================================

Use folder tools for local folders.

If a folder path has already been resolved, reuse it.

WHATSAPP MEDIA FILE RULES:

When the user asks to send a local file, screenshot, image,
video, document, audio file, or any other media through WhatsApp:

1. The WhatsApp MCP send_file/send_audio_message tools can only
   access files inside the configured WhatsApp media roots.

2. The default WhatsApp outbound media directory is:

   C:\\Users\\dhanu\\.local\\share\\whatsapp-mcp\\outbox

3. If the requested media file is outside the WhatsApp media directory,
   first use the local file copy tool to copy the file into:

   C:\\Users\\dhanu\\.local\\share\\whatsapp-mcp\\outbox

4. After copying, pass the COPIED FILE PATH to the WhatsApp MCP
   send_file/send_audio_message tool.

5. Do NOT attempt to send the original path directly when it is
   outside the WhatsApp media directory.

6. Preserve the original filename when copying whenever possible.

7. The copied file is only a temporary WhatsApp sending copy.
   Do not delete or modify the user's original file.

Example:

User:
"Send my screenshot to Ravi on WhatsApp."

Correct flow:

Screenshot:
C:\\Users\\dhanu\\Desktop\\Screenshot.png

Copy to:
C:\\Users\\dhanu\\.local\\share\\whatsapp-mcp\\outbox\\Screenshot.png

Then:
WhatsApp send_file(
    recipient=Ravi,
    file_path="C:\\Users\\dhanu\\.local\\share\\whatsapp-mcp\\outbox\\Screenshot.png"
)

Never send the original Desktop path directly if it is outside
the configured WhatsApp media roots.


============================================================
APPLICATIONS
============================================================

Use application tools for applications and opening files/folders
with applications.


============================================================
SYSTEM
============================================================

Use system tools for:

volume
brightness
Wi-Fi
Bluetooth
screenshots
etc.


============================================================
BROWSER
============================================================

Use browser tools for browser interaction.


============================================================
WEB
============================================================

Use web search when current internet information is required.


============================================================
TERMINAL
============================================================

Use terminal only when the user explicitly requests terminal/
command-line operations or when terminal execution is required.

============================================================
CODING
============================================================

A dedicated coding tool is available through the "coding" group.

Use the coding tool ONLY when the user's request requires
software engineering work such as:

- writing code
- creating code
- modifying code
- debugging code
- fixing code errors
- implementing features
- refactoring code
- building a software project
- running or fixing tests
- analyzing a codebase for development purposes

The coding tool uses its own specialized DeepSeek/LLM model
instance optimized for coding and software-engineering tasks.

IMPORTANT:

A single user request may require MORE THAN ONE tool group.

Select ALL tool groups required to complete the user's
CURRENT remaining action.

Do NOT stop after selecting the first obviously relevant group.

For coding tasks involving an existing local file, select:

file
coding

when both local-file access and software-engineering work
are required.

The "file" group is responsible for locating, retrieving,
or accessing an existing local file.

The "coding" group is responsible for software-engineering
work such as reading code for development, modifying code,
debugging, running, testing, and fixing code through the
dedicated coding agent.

If the required file path has already been resolved and no
file-tool operation is still required, reuse that exact path
and do not select "file" merely because the task involves a file.

Select groups based on the actual capabilities required by
the CURRENT action.

Do NOT select the coding group for normal questions,
explanations, file management without coding,
folder management, application control, messaging,
web search, browser tasks, system controls, or other
non-coding requests.

The coding tool should be used only when actual
software-engineering work is required.

============================================================
GOOGLE
============================================================

Google services are separated into groups.

Gmail:
email, inbox, attachments, send/reply email

Calendar:
events, meetings, schedules, appointments

Drive:
Google Drive files, upload, download, search

Docs:
Google Docs

Sheets:
Google Sheets

Tasks:
Google Tasks

People:
Google Contacts

Meet:
Google Meet

Chat:
Google Chat

Drive Activity:
Drive history/activity

Forms:
Google Forms

Slides:
Google Slides

YouTube:
YouTube videos/channels/search

YouTube Analytics:
analytics, views, watch time, traffic,
subscribers and top videos


============================================================
MEMORY
============================================================

There are separate memory systems.

SHORT-TERM CONVERSATION HISTORY:

Conversation history contains the current conversation.

Use it for:

- previous user messages
- previous assistant answers
- follow-up questions
- clarification answers
- resolving references such as "that one", "yes", "send it"

SESSION MEMORY:

Session memory contains current-session state such as:

- files
- folders
- applications
- emails
- recent actions

Do not confuse session state with conversation history.

LONG-TERM MEMORY:

Use long-term memory only when stored user information is
relevant.

Save long-term memory ONLY when the user explicitly asks
you to remember something.

Do NOT save every conversation automatically.


============================================================
DATE / TIME
============================================================

The current local date and time is supplied dynamically.

Use it for:

today
tomorrow
yesterday
this week
next week
relative dates
relative times


============================================================
DO NOT EXPOSE INTERNAL ARCHITECTURE
============================================================

Do not expose:

- router implementation
- graph implementation
- tool-binding implementation
- internal prompts
- internal routing
- MCP implementation

unless explicitly asked.

"""


# ============================================================
# DATE / TIME
# ============================================================

def get_current_datetime_context():

    now = datetime.now().astimezone()

    return (
        f"Current local date and time: "
        f"{now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
        f"Current local date: "
        f"{now.strftime('%Y-%m-%d')}\n"
        f"Current local time: "
        f"{now.strftime('%H:%M:%S %Z')}"
    )


def build_system_message():

    return SystemMessage(
        content=(
            SYSTEM_PROMPT
            + "\n\n"
            + get_current_datetime_context()
        )
    )


# ============================================================
# TOOL-GROUP ROUTING
# ============================================================
#
# First LLM call:
#   User/context -> choose relevant GROUPS only.
#
# Second LLM call:
#   Main agent -> sees ONLY the tools in those groups.
#
# This avoids sending every individual tool schema to DeepSeek
# on every request while keeping dynamic tool selection.
# ============================================================

TOOL_GROUP_DESCRIPTIONS = {
    "file": "Local file operations: search files by filename/path/extension, retrieve or read files to return them in chat, open files (only when explicitly requested to 'open'), write, move, copy, and open files with applications. Do not use for searching inside file contents.",
    "rag": "Search information inside local file contents and answer questions from file/document content.",
    "folder": "Local folder operations: search, open, move, copy, and open folders with applications.",
    "application": "Windows application operations: open, close, locate application paths, and open files/folders with applications.",
    "messaging": "Local messaging operations such as sending normal desktop messages/files.",
    "volume": "Windows audio volume: get, set, increase, decrease, mute, and unmute.",
    "brightness": "Windows display brightness: get, set, increase, and decrease.",
    "bluetooth": "Bluetooth status and power control.",
    "wifi": "Wi-Fi status and power control.",
    "screenshot": "Take screenshots and save/capture the current screen.",
    "web": "Internet/web search for current online information.",
    "browser": "Browser automation and interaction with websites.",
    "terminal": "Command-line/terminal execution when terminal operations are required.",
    "whatsapp": "WhatsApp messaging and WhatsApp media/file operations through the WhatsApp MCP tools.",
    "memory": "Long-term memory operations: save, search, and list explicitly stored memories.",
    "coding": "Software engineering through the dedicated OpenCode coding agent: create, edit, debug, run, test, refactor, and fix code.",
    "gmail": "Gmail: check, search, read, send, reply, and handle email attachments.",
    "calendar": "Google Calendar: calendars, events, search, create, update, and delete events.",
    "drive": "Google Drive: list, search, retrieve, download, and upload files.",
    "docs": "Google Docs: create, read, append, insert, replace, and delete document text.",
    "sheets": "Google Sheets: create, read, write, append, and clear spreadsheet data.",
    "tasks": "Google Tasks: task lists and create, update, complete, and delete tasks.",
    "people": "Google Contacts/People: list, search, and retrieve contacts.",
    "meet": "Google Meet: create, inspect, and end meeting spaces.",
    "chat": "Google Chat: spaces and messages, including send, update, and delete operations.",
    "drive_activity": "Google Drive Activity/history for files and Drive activity information.",
    "forms": "Google Forms: create and retrieve forms.",
    "slides": "Google Slides operations.",
    "youtube": "YouTube search and video/channel operations.",
    "youtube_analytics": "YouTube Analytics such as views, watch time, traffic sources, subscribers, and top videos.",
}

VALID_TOOL_GROUPS = set(TOOL_GROUPS.keys())

GROUP_ROUTER_PROMPT = """
You are the lightweight tool-group selector for a Windows AI desktop assistant.

Your job is ONLY to decide which tool GROUPS are required for the user's CURRENT
remaining action. Do not choose individual tools.

Use the conversation, session state, and long-term memory context to understand
follow-ups such as 'that file', 'the second one', 'send it', 'tomorrow', or 'yes'.
If an object was already resolved, do not select a group merely to rediscover it.
Select ALL groups needed for the remaining action, and no unnecessary groups.

If the request requires no tool, do NOT call the group-selection tool; answer the
user directly and briefly instead.

Available groups:
""" + "\n".join(
    f"- {name}: {description}"
    for name, description in TOOL_GROUP_DESCRIPTIONS.items()
)


def _request_tool_groups(groups: list[str]) -> str:
    """Internal routing function. The returned value is not executed as a tool."""
    valid = [group for group in groups if group in VALID_TOOL_GROUPS]
    return json.dumps(valid)


TOOL_GROUP_SELECTOR = StructuredTool.from_function(
    func=_request_tool_groups,
    name="select_tool_groups",
    description=(
        "Select the tool groups required for the user's current remaining action. "
        "Return one or more exact group names from the available group list."
    ),
)

TOOL_GROUP_LLM = llm.bind_tools(
    [TOOL_GROUP_SELECTOR]
)


# ============================================================
# SELECT TOOLS
# ============================================================

def get_selected_tools(selected_groups):

    selected_tools = []

    for group in selected_groups:
        selected_tools.extend(
            TOOL_GROUPS.get(group, [])
        )

    unique_tools = []
    seen = set()

    for tool in selected_tools:
        name = getattr(tool, "name", str(tool))
        if name not in seen:
            seen.add(name)
            unique_tools.append(tool)

    return unique_tools


# ============================================================
# CONTEXT MANAGEMENT
# ============================================================

# Keep the overall context bounded.  More importantly, do not keep
# sending the entire conversation history when session memory already
# contains resolved files, contacts, paths, IDs, and recent actions.
MAX_CONTEXT_TOKENS = 8000
SESSION_MEMORY_RESERVE = 1500
LONG_TERM_MEMORY_RESERVE = 800

# The router only needs enough recent dialogue to resolve short
# follow-ups/clarifications.  The main agent gets a little more context
# for multi-step tasks.  Both still have session memory available.
MAX_ROUTER_HISTORY_MESSAGES = 6
MAX_AGENT_HISTORY_MESSAGES = 10


def _safe_memory_text(memory_object):
    try:
        return memory_object.to_text()
    except Exception as exc:
        print(f"[Memory] Context warning: {exc}")
        return "No memory context available."


def _recent_conversation_history(conversation_history, max_messages):
    """Return only the most recent complete messages for one conversation."""

    if not conversation_history:
        return []

    history = conversation_history[-max_messages:]

    if len(history) > 1 and isinstance(history[0], AIMessage):
        history = history[1:]

    return history


def get_context_messages(
    user_input,
    conversation_history,
    session_memory,
    history_limit=MAX_AGENT_HISTORY_MESSAGES,
):
    """
    Build a bounded context snapshot for one LLM pipeline.

    Session/long-term memory are kept separate from conversation history.
    Raw conversation history is deliberately limited because resolved state
    is already recorded in session memory.
    """

    session_text = _safe_memory_text(session_memory)
    long_term_text = _safe_memory_text(long_term_memory)

    session_message = SystemMessage(
        content="SESSION MEMORY:\n" + session_text
    )

    long_term_message = SystemMessage(
        content="LONG-TERM MEMORY:\n" + long_term_text
    )

    recent_history = _recent_conversation_history(
        conversation_history,
        history_limit,
    )

    return [
        build_system_message(),
        long_term_message,
        session_message,
        *recent_history,
        HumanMessage(content=user_input),
    ]


def trim_agent_context(messages):
    """Final safety trim before an LLM call, keeping system context."""
    try:
        return trim_messages(
            messages,
            max_tokens=MAX_CONTEXT_TOKENS,
            strategy="last",
            token_counter=llm,
            include_system=True,
            start_on="human",
            allow_partial=False,
        )
    except Exception:
        # Preserve system messages and the most recent dialogue if token
        # counting is unavailable.
        system_messages = [
            message
            for message in messages
            if isinstance(message, SystemMessage)
        ]
        other_messages = [
            message
            for message in messages
            if not isinstance(message, SystemMessage)
        ]
        return system_messages + other_messages[-12:]


# ============================================================
# TOOL-GROUP ROUTER
# ============================================================

def choose_tool_groups(context_messages):

    router_messages = [
        SystemMessage(
            content=(
                SYSTEM_PROMPT
                + "\n\n"
                + GROUP_ROUTER_PROMPT
            )
        ),
        *context_messages[1:],
    ]

    response = TOOL_GROUP_LLM.invoke(
        trim_agent_context(router_messages)
    )

    tool_calls = getattr(response, "tool_calls", []) or []

    if not tool_calls:
        # No tools required. The router's content can be used as
        # the final answer for simple conversational requests.
        return [], response.content or ""

    selected_groups = []

    for tool_call in tool_calls:
        if tool_call.get("name") != "select_tool_groups":
            continue

        args = tool_call.get("args", {}) or {}
        groups = args.get("groups", []) or []

        for group in groups:
            if group in VALID_TOOL_GROUPS and group not in selected_groups:
                selected_groups.append(group)

    return selected_groups, None


# ============================================================
# DYNAMIC AGENT GRAPH CACHE
# ============================================================

AGENT_GRAPH_CACHE = {}


def create_agent_graph(selected_groups):

    key = tuple(sorted(set(selected_groups)))

    if not key:
        return None

    if key in AGENT_GRAPH_CACHE:
        return AGENT_GRAPH_CACHE[key]

    selected_tools = get_selected_tools(key)

    if not selected_tools:
        return None

    selected_llm = llm.bind_tools(selected_tools)
    selected_tool_node = ToolNode(selected_tools)

    def call_model(state):
        response = selected_llm.invoke(
            trim_agent_context(state["messages"])
        )
        return {
            "messages": [response]
        }

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", selected_tool_node)
    graph.add_edge(START, "model")
    graph.add_conditional_edges(
        "model",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )
    graph.add_edge("tools", "model")

    compiled = graph.compile()
    AGENT_GRAPH_CACHE[key] = compiled

    return compiled


# ============================================================
# SESSION MEMORY UPDATE
# ============================================================

def update_session_memory(messages, session_memory):

    tool_names_by_id = {}

    for message in messages:
        if isinstance(message, AIMessage):
            for tool_call in getattr(message, "tool_calls", []) or []:
                tool_name = tool_call.get("name")
                tool_call_id = tool_call.get("id")
                if tool_name:
                    try:
                        session_memory.record_tool_call(
                            tool_name,
                            tool_call.get("args", {}) or {},
                        )
                    except Exception as exc:
                        print(f"[Memory] Tool-call warning: {exc}")
                    if tool_call_id:
                        tool_names_by_id[tool_call_id] = tool_name

        elif isinstance(message, ToolMessage):
            tool_name = getattr(message, "name", None)
            if not tool_name:
                tool_name = tool_names_by_id.get(
                    getattr(message, "tool_call_id", None)
                )
            if tool_name:
                try:
                    session_memory.record_tool_result(
                        tool_name,
                        message.content,
                    )
                except Exception as exc:
                    print(f"[Memory] Tool-result warning: {exc}")


# ============================================================
# CONVERSATION HISTORY
# ============================================================

# Conversation history is loaded from SQLite for each request.
# There is intentionally no global conversation_history list here.


# ============================================================
# RECORD SESSION STATE
# ============================================================

def record_session_action(
    tool_name,
    arguments,
    result=None,
    conversation_id=0,
):

    session_memory = get_session_memory(conversation_id)

    try:

        session_memory.record_tool_call(
            tool_name,
            arguments,
        )

        if result is not None:

            session_memory.record_tool_result(
                tool_name,
                result,
            )

    except Exception as e:

        print(
            f"[Memory] Session state warning: {e}"
        )


# ============================================================
# SCREEN CONTEXT TRIGGER
# ============================================================

# Screen context is expensive because prepare_screen_context() may call
# an LLM and/or capture/analyze the current screen.  Only invoke it when
# the user's wording actually refers to the visible UI/current window.
# This is NOT intent detection for tool selection; it only decides whether
# screen context is necessary. The normal group router still decides tools.
SCREEN_CONTEXT_PHRASES = (
    "open this",
    "click this",
    "what is on my screen",
    "what's on my screen",
    "what is on the screen",
    "what's on the screen",
    "look at the current window",
    "look at my current window",
    "look at this window",
    "look at my screen",
    "what application is open",
    "what app is open",
    "what application is currently open",
    "what app is currently open",
    "current window",
    "current application",
    "current app",
    "this window",
    "this file",
    "this folder",
    "the file i'm viewing",
    "the file im viewing",
    "the folder i'm viewing",
    "the folder im viewing",
    "the file i'm looking at",
    "the file im looking at",
    "the folder i'm looking at",
    "the folder im looking at",
    "send the file i'm viewing",
    "send the file im viewing",
    "open this folder in vscode",
    "open this folder in vs code",
    "open this folder in visual studio code",
    "open this file in vscode",
    "open this file in vs code",
    "open this file in visual studio code",
)


def needs_screen_context(user_input):
    """Return True only when the request explicitly references the UI/screen."""

    text = " ".join(user_input.lower().split())

    return any(
        phrase in text
        for phrase in SCREEN_CONTEXT_PHRASES
    )


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent(
    user_input,
    conversation_id=0,
    db_messages=None,
):

    raw_user_input = user_input.strip()

    if not raw_user_input:
        return "Please provide a request."

    # Each chat gets its own session memory.
    session_memory = get_session_memory(conversation_id)

    # Conversation history is loaded from the database by backend.chat.
    # Convert database rows into LangChain message objects.
    conversation_history = []

    for row in db_messages or []:
        role = row.get("role")
        content = row.get("content", "")

        if not content:
            continue

        if role == "user":
            conversation_history.append(
                HumanMessage(content=content)
            )
        elif role == "assistant":
            conversation_history.append(
                AIMessage(content=content)
            )

    # --------------------------------------------------------
    # Screen context is now ON-DEMAND.
    #
    # Normal requests do NOT pay for the screen-context LLM call.
    # It is only activated for explicit screen/current-window/UI
    # references such as "open this", "click this", or
    # "what application is open".
    # --------------------------------------------------------

    if needs_screen_context(raw_user_input):
        print("[Screen context] Triggered")
        contextualized_input = prepare_screen_context(
            raw_user_input
        )
    else:
        print("[Screen context] Skipped")
        contextualized_input = raw_user_input

    # --------------------------------------------------------
    # STEP 1: Build a SMALL context for the group router.
    #
    # The router does not need the full conversation. Session memory
    # already contains resolved state, so only the most recent few
    # dialogue messages are retained here.
    # --------------------------------------------------------

    router_context_messages = get_context_messages(
        contextualized_input,
        conversation_history=conversation_history,
        session_memory=session_memory,
        history_limit=MAX_ROUTER_HISTORY_MESSAGES,
    )

    selected_groups, direct_answer = choose_tool_groups(
        router_context_messages
    )

    print(
        f"[Tool groups selected] "
        f"{', '.join(selected_groups) if selected_groups else 'none'}"
    )

    # Simple conversational request: router answered directly,
    # so avoid a second LLM call.
    if not selected_groups:

        answer = direct_answer.strip() if direct_answer else ""

        if not answer:
            answer = "I couldn't generate a response."

        return answer

    # --------------------------------------------------------
    # STEP 2: load ONLY tools from selected groups.
    # --------------------------------------------------------

    graph = create_agent_graph(
        selected_groups
    )

    if graph is None:
        answer = "I couldn't load the required tools."
        return answer

    # --------------------------------------------------------
    # STEP 3: Build the main-agent context.
    #
    # Give the execution model a few more recent messages than the
    # router, but still avoid replaying the entire conversation.
    # --------------------------------------------------------

    agent_context_messages = get_context_messages(
        contextualized_input,
        conversation_history=conversation_history,
        session_memory=session_memory,
        history_limit=MAX_AGENT_HISTORY_MESSAGES,
    )

    # --------------------------------------------------------
    # STEP 4: run the normal iterative model -> tools -> model
    # loop using only the selected tool set.
    # --------------------------------------------------------

    result = graph.invoke(
        {
            "messages": agent_context_messages
        },
        config={
            "recursion_limit": 20,
        },
    )

    result_messages = result.get(
        "messages",
        [],
    )

    # --------------------------------------------------------
    # Record only messages created during this request.
    # --------------------------------------------------------

    new_messages = result_messages[
        len(agent_context_messages):
    ]

    update_session_memory(
        new_messages,
        session_memory,
    )

    # --------------------------------------------------------
    # Find final AI response.
    # --------------------------------------------------------

    answer = None

    for message in reversed(result_messages):
        if isinstance(message, AIMessage) and message.content:
            answer = message.content
            break

    if answer is None:
        answer = "I couldn't generate a response."

    # --------------------------------------------------------
    # Ensure any media/image filepaths returned by tools during
    # this turn are included in the final answer for UI rendering.
    # --------------------------------------------------------
    import re
    img_pattern = re.compile(
        r'([A-Za-z]:\\[^\s\n"\'\(\)]+\.(?:png|jpg|jpeg|gif|webp|svg)|'
        r'[A-Za-z]:/[^\s\n"\'\(\)]+\.(?:png|jpg|jpeg|gif|webp|svg))',
        re.IGNORECASE,
    )

    missing_images = []
    for msg in new_messages:
        if isinstance(msg, ToolMessage) and msg.content:
            matches = img_pattern.findall(str(msg.content))
            for path in matches:
                normalized = path.replace("\\", "/")
                # Check if an actual markdown image tag already exists for this image in the answer
                has_image_tag = bool(
                    re.search(r'!\[.*?\]\([^\)]*' + re.escape(normalized) + r'[^\)]*\)', answer, re.IGNORECASE)
                    or re.search(r'!\[.*?\]\([^\)]*' + re.escape(path) + r'[^\)]*\)', answer, re.IGNORECASE)
                )
                if not has_image_tag and normalized not in missing_images:
                    missing_images.append(normalized)

    if missing_images:
        images_markdown = "\n\n" + "\n\n".join(
            f"![Screenshot]({p})" for p in missing_images
        )
        answer = answer.strip() + images_markdown

    # Ensure other document/code/data files returned by tools are included as file attachment cards
    file_pattern = re.compile(
        r'([A-Za-z]:\\[^\s\n"\'\(\)]+\.[a-zA-Z0-9]{1,10}|'
        r'[A-Za-z]:/[^\s\n"\'\(\)]+\.[a-zA-Z0-9]{1,10})',
        re.IGNORECASE,
    )
    missing_files = []
    for msg in new_messages:
        if isinstance(msg, ToolMessage) and msg.content:
            matches = file_pattern.findall(str(msg.content))
            for path in matches:
                normalized = path.replace("\\", "/")
                basename = normalized.split("/")[-1]
                ext = basename.split(".")[-1].lower() if "." in basename else ""
                if ext in {"png", "jpg", "jpeg", "gif", "webp", "svg"}:
                    continue
                has_file_tag = bool(
                    re.search(r'\[.*?\]\([^\)]*' + re.escape(normalized) + r'[^\)]*\)', answer, re.IGNORECASE)
                    or re.search(r'\[.*?\]\([^\)]*' + re.escape(path) + r'[^\)]*\)', answer, re.IGNORECASE)
                )
                if not has_file_tag and normalized not in missing_files:
                    missing_files.append(normalized)

    if missing_files:
        files_markdown = "\n\n" + "\n\n".join(
            f"[{p.split('/')[-1]}]({p})" for p in missing_files
        )
        answer = answer.strip() + files_markdown

    # --------------------------------------------------------
    # Save ONLY the real user turn and final assistant answer.
    # Tool calls/results remain in session memory and are not
    # duplicated into long-term conversation history.
    # --------------------------------------------------------

    return answer


# ============================================================
# TERMINAL
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "LOCAL AI DESKTOP AGENT"
    )

    print("=" * 60)

    print(
        "Dynamic Tool-Group Selection Enabled"
    )

    print(
        "Selected-Tool Agent Loop Enabled"
    )

    print(
        f"Tool Groups Available: {len(TOOL_GROUPS)}"
    )

    print(
        "Short-Term Conversation Context Enabled"
    )

    print(
        "Session Memory Enabled"
    )

    print(
        "Long-Term Memory Tools Enabled"
    )

    print(
        "Date/Time Context Enabled"
    )

    print(
        "WhatsApp MCP Enabled"
    )

    print(
        f"WhatsApp MCP Tools: "
        f"{len(WHATSAPP_TOOLS)}"
    )

    print(
        "Type 'exit' to quit."
    )

    print("=" * 60)

    while True:

        try:

            user_input = input(
                "\nYou: "
            ).strip()

        except KeyboardInterrupt:

            print(
                "\nExiting..."
            )

            break

        except EOFError:

            print(
                "\nExiting..."
            )

            break

        if user_input.lower() in {
            "exit",
            "quit",
        }:

            print(
                "Exiting..."
            )

            stop_whatsapp_bridge()

            break

        try:

            response = run_agent(
                user_input
            )

            print(
                f"\nAgent: {response}"
            )

        except Exception as e:

            print(
                f"\nAgent Error: {e}"
            )