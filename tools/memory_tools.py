from langchain_core.tools import tool

from memory.long_term_memory import LongTermMemory


# =========================================================
# MEMORY INSTANCE
# =========================================================

memory = LongTermMemory()


# =========================================================
# SAVE MEMORY
# =========================================================

@tool
def save_memory(
    memory_text: str,
    category: str = "general"
):
    """
    Save information when the user explicitly asks to remember it.
    """

    memory_text = memory_text.strip()

    if not memory_text:
        return "Memory text cannot be empty."

    saved = memory.save(
        memory_text,
        category=category
    )

    if saved:
        return "Memory saved."

    return "Memory already exists."


# =========================================================
# SEARCH LONG-TERM MEMORY
# =========================================================

@tool
def search_long_term_memory(
    keyword: str,
    limit: int = 3
):
    """
    Search saved user information when needed to answer a request.
    """

    keyword = keyword.strip()

    if not keyword:
        return "No search query provided."

    # Keep memory results small
    limit = min(max(limit, 1), 5)

    results = memory.search(
        keyword,
        limit=limit
    )

    if not results:
        return "No matching memories."

    return "\n".join(
        f"[{category}] {memory_text}"
        for _, memory_text, category, _ in results
    )


# =========================================================
# GET ALL LONG-TERM MEMORY
# =========================================================

@tool
def get_all_memories():
    """
    Return all saved memories.
    """

    results = memory.get_all()

    if not results:
        return "No stored memories."

    return "\n".join(
        f"[{category}] {memory_text}"
        for _, memory_text, category, _ in results
    )