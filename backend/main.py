import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.chat import process_chat_message
from backend.database import (
    create_conversation,
    get_conversations,
    get_messages,
    add_message,
    update_conversation_title,
)


# ============================================================
# LOGGING FILTER
# ============================================================
# Suppress repetitive background request logs (/health & /dom)

class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        log_message = record.getMessage()
        return "/health" not in log_message and "/dom" not in log_message


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Local AI Agent Backend",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================
#
# Supports:
#   - React/Vite localhost
#   - 127.0.0.1
#   - Tauri v2
#
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        # Vite localhost
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",

        # Vite 127.0.0.1
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",

        # Tauri
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],

    # Allows localhost, tauri, and external origins (e.g. Chrome extensions running on web pages).
    allow_origin_regex=r".*",

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# CORS DEBUG
# ============================================================

@app.middleware("http")
async def debug_cors(request, call_next):

    if request.method == "OPTIONS":

        print("\n========== CORS DEBUG ==========")

        print("METHOD:", request.method)

        print("PATH:", request.url.path)

        print(
            "ORIGIN:",
            request.headers.get("origin"),
        )

        print(
            "ACCESS-CONTROL-REQUEST-METHOD:",
            request.headers.get(
                "access-control-request-method"
            ),
        )

        print(
            "ACCESS-CONTROL-REQUEST-HEADERS:",
            request.headers.get(
                "access-control-request-headers"
            ),
        )

        print("================================\n")

    response = await call_next(request)

    return response


# ============================================================
# REQUEST MODELS
# ============================================================


class ChatRequest(BaseModel):
    conversation_id: int
    message: str


class ChatResponse(BaseModel):
    response: str


class MessageRequest(BaseModel):
    role: str
    content: str


class ConversationTitleRequest(BaseModel):
    title: str


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "Local AI Agent Backend",
    }


# ============================================================
# CONVERSATIONS
# ============================================================


@app.post("/chats")
def new_chat():

    conversation_id = create_conversation()

    return {
        "id": conversation_id,
        "title": "New Chat",
    }


@app.get("/chats")
def chats():

    return get_conversations()


@app.get("/chats/{conversation_id}/messages")
def chat_messages(
    conversation_id: int,
):

    return get_messages(conversation_id)


@app.post("/chats/{conversation_id}/messages")
def add_chat_message(
    conversation_id: int,
    request: MessageRequest,
):

    add_message(
        conversation_id,
        request.role,
        request.content,
    )

    return {
        "status": "saved",
    }


@app.patch("/chats/{conversation_id}/title")
def rename_chat(
    conversation_id: int,
    request: ConversationTitleRequest,
):

    title = request.title.strip()

    if not title:
        title = "New Chat"

    title = title[:80]

    update_conversation_title(
        conversation_id,
        title,
    )

    return {
        "status": "updated",
        "title": title,
    }


# ============================================================
# AGENT CHAT
# ============================================================


@app.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
):

    response = process_chat_message(
        conversation_id=request.conversation_id,
        user_input=request.message,
    )

    return {
        "response": response,
    }


# ============================================================
# DOM ENDPOINT (for Chrome extension / DOM extraction)
# ============================================================


@app.post("/dom")
def receive_dom(payload: dict = None):
    """Handles DOM data sent by browser extensions or DOM services."""
    return {"status": "ok"}


@app.options("/dom")
def options_dom():
    """Fallback options handler for /dom if needed."""
    return {"status": "ok"}



# ============================================================
# STARTUP
# ============================================================


@app.on_event("startup")
async def startup_event():

    print("\n========================================")
    print(" Local AI Agent Backend")
    print("========================================")
    print(" FastAPI server started")
    print(" API: http://127.0.0.1:8000")
    print(" Health: http://127.0.0.1:8000/health")
    print("========================================\n")