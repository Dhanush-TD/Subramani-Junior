from langchain_core.tools import tool

from tools.rag_tools import find_file_with_rag


@tool
def search_file_by_content(query: str):
    """
    Find a local file by its content/topic when no exact filename is given.
    Returns the best matching file path.
    """
    return find_file_with_rag(query)