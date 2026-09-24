from backend.database import get_messages


def process_chat_message(
    conversation_id: int,
    user_input: str,
) -> str:
    """Process a message using only the selected conversation's context."""

    if not user_input or not user_input.strip():
        return "Please provide a message."

    if not conversation_id:
        return "Invalid conversation."

    from agent import run_agent

    # The frontend saves the current user message before calling /chat.
    # Load the conversation from SQLite, then remove that just-saved turn
    # because run_agent adds the current input separately to the LLM context.
    db_messages = get_messages(conversation_id)

    if db_messages:
        last = db_messages[-1]
        if (
            last.get("role") == "user"
            and last.get("content", "").strip() == user_input.strip()
        ):
            db_messages = db_messages[:-1]

    return run_agent(
        user_input=user_input.strip(),
        conversation_id=conversation_id,
        db_messages=db_messages,
    )
