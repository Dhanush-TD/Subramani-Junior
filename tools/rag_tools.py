import sys
from pathlib import Path


# ============================================================
# EXISTING RAG PROJECT
# ============================================================

RAG_PROJECT = Path(
    r"C:\Users\dhanu\RGG\rag_file_search_fixed"
).resolve()


# ============================================================
# VERIFY RAG PROJECT
# ============================================================

if not RAG_PROJECT.exists():
    raise RuntimeError(
        f"RAG project not found:\n{RAG_PROJECT}"
    )


# ============================================================
# ADD RAG PROJECT TO PYTHON PATH
# ============================================================

if str(RAG_PROJECT) not in sys.path:
    sys.path.insert(0, str(RAG_PROJECT))


# ============================================================
# IMPORT RAG MODULES
# ============================================================

import database
import vector_store

from hybrid_search import hybrid_search


# ============================================================
# FORCE RAG TO USE ITS OWN DATABASE
# ============================================================

database.DB_PATH = (
    RAG_PROJECT
    / "data"
    / "rag.db"
)


# ============================================================
# FORCE RAG TO USE ITS OWN FAISS INDEX
# ============================================================

vector_store.INDEX_PATH = (
    RAG_PROJECT
    / "data"
    / "vectors.faiss"
)


# ============================================================
# PATHS
# ============================================================

RAG_DATABASE = database.DB_PATH
RAG_VECTOR_INDEX = vector_store.INDEX_PATH


# ============================================================
# DEBUG INFORMATION
# ============================================================

print()
print("========================================")
print(" RAG CONNECTION")
print("========================================")
print(f"RAG project : {RAG_PROJECT}")
print(f"Database    : {RAG_DATABASE}")
print(f"FAISS index : {RAG_VECTOR_INDEX}")
print("========================================")
print()


# ============================================================
# VERIFY RAG FILES
# ============================================================

def verify_rag():

    # --------------------------------------------------------
    # Check database
    # --------------------------------------------------------

    if not RAG_DATABASE.is_file():

        return (
            False,
            f"RAG database not found:\n"
            f"{RAG_DATABASE}"
        )


    # --------------------------------------------------------
    # Check FAISS index
    # --------------------------------------------------------

    if not RAG_VECTOR_INDEX.is_file():

        return (
            False,
            f"RAG vector index not found:\n"
            f"{RAG_VECTOR_INDEX}"
        )


    return True, "RAG files verified."


# ============================================================
# FIND FILE USING EXISTING RAG
# ============================================================

def find_file_with_rag(query: str) -> str:

    """
    Search the existing RAG and return the best matching
    local file path.

    This function DOES NOT create a new RAG.

    It uses:

        C:\\Users\\dhanu\\RGG\\rag_file_search_fixed

    and its existing:

        data/rag.db
        data/vectors.faiss
        Qwen embedding model
    """

    # ========================================================
    # VALIDATE QUERY
    # ========================================================

    if not query or not query.strip():

        return "No file search query was provided."


    query = query.strip()


    # ========================================================
    # VERIFY RAG
    # ========================================================

    ok, message = verify_rag()

    if not ok:

        print("[RAG] Verification failed.")
        print(message)

        return message


    # ========================================================
    # SEARCH
    # ========================================================

    print()
    print("========================================")
    print("[RAG] Searching for file...")
    print(f"[RAG] Query: {query}")
    print("========================================")


    try:

        # ----------------------------------------------------
        # CALL EXISTING RAG
        # ----------------------------------------------------

        results = hybrid_search(query)


        # ----------------------------------------------------
        # NO RESULTS
        # ----------------------------------------------------

        if not results:

            print("[RAG] No results found.")

            return (
                f"No file found for query: "
                f"{query}"
            )


        # ====================================================
        # SHOW RESULTS
        # ====================================================

        print()
        print("[RAG] Search results:")

        for index, result in enumerate(
            results[:5],
            start=1
        ):

            print(
                f"{index}. "
                f"{result.get('filename', 'Unknown')}"
            )

            print(
                f"   Path: "
                f"{result.get('path', 'Unknown')}"
            )

            print(
                f"   Score: "
                f"{result.get('reranker_score', 'N/A')}"
            )


        # ====================================================
        # BEST RESULT
        # ====================================================

        best_result = results[0]


        # ----------------------------------------------------
        # GET PATH
        # ----------------------------------------------------

        file_path = best_result.get("path")


        # ----------------------------------------------------
        # GET FILENAME
        # ----------------------------------------------------

        filename = best_result.get(
            "filename",
            "Unknown file"
        )


        # ----------------------------------------------------
        # PATH MISSING
        # ----------------------------------------------------

        if not file_path:

            return (
                "RAG found a result, "
                "but no file path was returned."
            )


        # ====================================================
        # NORMALIZE PATH
        # ====================================================

        file_path = Path(
            file_path
        ).resolve()


        print()
        print(
            f"[RAG] Best match: {filename}"
        )

        print(
            f"[RAG] File path: {file_path}"
        )


        # ====================================================
        # VERIFY FILE EXISTS
        # ====================================================

        if not file_path.is_file():

            print(
                "[RAG] WARNING: "
                "File does not exist."
            )

            return (
                f"RAG found '{filename}', "
                f"but the file no longer exists:\n"
                f"{file_path}"
            )


        # ====================================================
        # SUCCESS
        # ====================================================

        print(
            "[RAG] File verified successfully."
        )

        print(
            "========================================"
        )
        print(
            "[RAG] SEARCH SUCCESS"
        )
        print(
            "========================================"
        )


        return str(file_path)


    # ========================================================
    # ERROR
    # ========================================================

    except Exception as e:

        print()
        print(
            "[RAG] Search failed:"
        )

        print(
            repr(e)
        )

        return (
            f"RAG file search failed: {e}"
        )


# ============================================================
# OPTIONAL - RETURN FULL SEARCH RESULTS
# ============================================================

def search_files_with_rag(
    query: str,
    top_k: int = 5
):

    """
    Return multiple RAG results instead of only
    the best file.

    Useful later when the agent needs to choose
    between several files.
    """

    if not query or not query.strip():

        return []


    query = query.strip()


    try:

        results = hybrid_search(query)


        if not results:

            return []


        output = []


        for result in results[:top_k]:

            file_path = result.get("path")


            if not file_path:

                continue


            output.append({

                "filename":
                    result.get(
                        "filename",
                        ""
                    ),

                "path":
                    str(
                        Path(
                            file_path
                        ).resolve()
                    ),

                "score":
                    result.get(
                        "reranker_score"
                    ),

                "page":
                    result.get(
                        "page"
                    ),

                "chunk_id":
                    result.get(
                        "chunk_id"
                    ),

            })


        return output


    except Exception as e:

        print(
            f"[RAG] Multi-search failed: "
            f"{repr(e)}"
        )

        return []


# ============================================================
# TEST
# ============================================================

def test_rag():

    print()
    print("========================================")
    print(" RAG TEST")
    print("========================================")


    # --------------------------------------------------------
    # Verify files
    # --------------------------------------------------------

    ok, message = verify_rag()


    if not ok:

        print("[FAIL]", message)

        return False


    print("[PASS]", message)


    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    query = "test file"


    print()
    print(
        f"[TEST] Query: {query}"
    )


    result = find_file_with_rag(
        query
    )


    print()
    print("========================================")
    print(" FINAL RESULT")
    print("========================================")


    print(result)


    # --------------------------------------------------------
    # Determine success
    # --------------------------------------------------------

    if result.startswith(
        "RAG file search failed:"
    ):

        return False


    if result.startswith(
        "No file found"
    ):

        return False


    if result.startswith(
        "RAG found"
    ):

        return False


    if Path(result).is_file():

        print()
        print(
            "[PASS] File found successfully."
        )

        return True


    print()
    print(
        "[FAIL] Returned path is not a file."
    )

    return False


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    success = test_rag()

    print()

    if success:

        print(
            "RAG TEST PASSED"
        )

    else:

        print(
            "RAG TEST FAILED"
        )