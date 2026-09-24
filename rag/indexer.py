import os
import shutil


from langchain_huggingface import (
    HuggingFaceEmbeddings
)

from langchain_community.vectorstores import (
    Chroma
)


from .config import (
    VECTOR_DB_DIR,
    EMBEDDING_MODEL,
)


from .file_loader import (
    scan_files,
    read_file,
)


from .chunker import (
    chunk_text,
)


# =========================================================
# EMBEDDING MODEL
# =========================================================

print(
    "[RAG] Loading embedding model..."
)


embeddings = HuggingFaceEmbeddings(

    model_name=EMBEDDING_MODEL

)


print(
    "[RAG] Embedding model loaded."
)


# =========================================================
# BUILD INDEX
# =========================================================

def build_index():

    """
    Scan files, read their contents,
    split them into chunks and create
    a local vector database.
    """

    documents = []


    total_files = 0

    successful_files = 0

    total_chunks = 0


    print()

    print(
        "======================================"
    )

    print(
        " RAG INDEXING"
    )

    print(
        "======================================"
    )

    print()


    # =====================================================
    # SCAN FILES
    # =====================================================

    for file_path in scan_files():

        total_files += 1


        print(
            f"[RAG] Reading: {file_path}"
        )


        # -------------------------------------------------
        # READ FILE
        # -------------------------------------------------

        text = read_file(
            file_path
        )


        if text is None:

            continue


        if not text.strip():

            print(
                "[RAG] Empty file - skipped."
            )

            continue


        successful_files += 1


        # -------------------------------------------------
        # CREATE CHUNKS
        # -------------------------------------------------

        chunks = chunk_text(

            text,

            file_path

        )


        if not chunks:

            continue


        documents.extend(
            chunks
        )


        total_chunks += len(
            chunks
        )


        print(
            f"[RAG]   Chunks: "
            f"{len(chunks)}"
        )


    # =====================================================
    # NO DOCUMENTS
    # =====================================================

    if not documents:

        print()

        print(
            "[RAG] No documents were found."
        )

        return False


    # =====================================================
    # CREATE RAG DATA DIRECTORY
    # =====================================================

    os.makedirs(

        os.path.dirname(
            VECTOR_DB_DIR
        ),

        exist_ok=True

    )


    # =====================================================
    # REMOVE OLD DATABASE
    # =====================================================
    #
    # IMPORTANT:
    #
    # This is only for our FIRST version.
    #
    # Later we will replace this with
    # incremental indexing.
    #
    # =====================================================

    if os.path.exists(
        VECTOR_DB_DIR
    ):

        print()

        print(
            "[RAG] Removing previous vector database..."
        )


        try:

            shutil.rmtree(
                VECTOR_DB_DIR
            )

        except Exception as e:

            print(
                "[RAG] Could not remove old database."
            )

            print(
                f"[RAG] Error: {e}"
            )

            return False


    # =====================================================
    # CREATE VECTOR DATABASE
    # =====================================================

    print()

    print(
        "[RAG] Creating vector database..."
    )

    print(
        "[RAG] This may take some time for many files."
    )


    try:

        vector_store = (
            Chroma.from_documents(

                documents=documents,

                embedding=embeddings,

                persist_directory=VECTOR_DB_DIR,

            )
        )

    except Exception as e:

        print()

        print(
            "[RAG] Failed to create vector database."
        )

        print(
            f"[RAG] Error: {e}"
        )

        return False


    # =====================================================
    # PERSIST
    # =====================================================

    try:

        vector_store.persist()

    except Exception:

        # Newer Chroma versions may automatically
        # persist the database.

        pass


    # =====================================================
    # RESULT
    # =====================================================

    print()

    print(
        "======================================"
    )

    print(
        " RAG INDEX COMPLETE"
    )

    print(
        "======================================"
    )

    print()

    print(
        f"Files discovered : {total_files}"
    )

    print(
        f"Files indexed    : {successful_files}"
    )

    print(
        f"Chunks created   : {total_chunks}"
    )

    print()

    print(
        f"Vector database:"
    )

    print(
        VECTOR_DB_DIR
    )

    print()

    return True


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    build_index()