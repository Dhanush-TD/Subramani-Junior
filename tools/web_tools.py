import os

from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_core.tools import tool


load_dotenv()


# =========================================================
# CONFIGURATION
# =========================================================

MAX_RESULTS = 5

# Maximum content returned for each search result.
# Prevents long webpages from consuming unnecessary
# DeepSeek tokens.
MAX_CONTENT_CHARS = 2500


# =========================================================
# TAVILY CLIENT
# =========================================================

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


# =========================================================
# CONTENT OPTIMIZATION
# =========================================================

def _truncate_content(
    content: str,
    max_chars: int = MAX_CONTENT_CHARS,
) -> str:
    """
    Limit webpage content returned to the LLM.

    Keeps the beginning and end of the content so useful
    information is less likely to be lost.
    """

    if not content:
        return ""

    content = content.strip()

    if len(content) <= max_chars:
        return content

    head_size = max_chars // 2
    tail_size = max_chars - head_size

    return (
        content[:head_size]
        + "\n\n"
        "[CONTENT TRUNCATED FOR TOKEN EFFICIENCY]\n\n"
        + content[-tail_size:]
    )


# =========================================================
# WEB SEARCH
# =========================================================

@tool
def web_search(query: str) -> str:
    """
    Search the web for current information.
    """

    if not query or not query.strip():
        return "Web search failed: query cannot be empty."

    try:

        response = client.search(
            query=query.strip(),
            search_depth="advanced",
            max_results=MAX_RESULTS,
        )

        results = response.get("results", [])

        if not results:
            return "No web results found."

        output = []

        for index, result in enumerate(results, start=1):

            title = result.get("title", "").strip()
            url = result.get("url", "").strip()
            content = result.get("content", "").strip()

            content = _truncate_content(content)

            output.append(
                f"Result {index}\n"
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Content: {content}"
            )

        return "\n\n---\n\n".join(output)

    except Exception as e:

        return f"Web search failed: {e}"