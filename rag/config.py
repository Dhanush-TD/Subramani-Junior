import os


# =========================================================
# RAG CONFIGURATION
# =========================================================


# =========================================================
# DIRECTORIES TO INDEX
# =========================================================
#
# These are the folders that the RAG system will scan.
#
# You can add more folders later.
#
# Example:
#
# r"D:\Projects"
# r"D:\local-file-agent"
#
# =========================================================

INDEX_DIRECTORIES = [

    os.path.expanduser(
        "~/Documents"
    ),

    os.path.expanduser(
        "~/Desktop"
    ),

    os.path.expanduser(
        "~/Downloads"
    ),

]


# =========================================================
# RAG DATA DIRECTORY
# =========================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


RAG_DATA_DIR = os.path.join(
    PROJECT_ROOT,
    "rag_data"
)


# =========================================================
# VECTOR DATABASE
# =========================================================

VECTOR_DB_DIR = os.path.join(
    RAG_DATA_DIR,
    "vector_db"
)


# =========================================================
# SUPPORTED FILE EXTENSIONS
# =========================================================
#
# Start with text/code based files.
#
# We will add PDF, DOCX, XLSX, images, etc.
# in the next stage.
#
# =========================================================

SUPPORTED_EXTENSIONS = {

    ".txt",
    ".md",

    ".py",
    ".js",
    ".ts",

    ".java",
    ".cpp",
    ".c",
    ".h",

    ".json",
    ".xml",

    ".html",
    ".css",

    ".csv",

    ".log",

}


# =========================================================
# FILE SIZE LIMIT
# =========================================================
#
# Prevent extremely large files from being loaded
# into memory at once.
#
# =========================================================

MAX_FILE_SIZE_MB = 10


# =========================================================
# CHUNKING
# =========================================================

CHUNK_SIZE = 1000

CHUNK_OVERLAP = 150


# =========================================================
# EMBEDDING MODEL
# =========================================================
#
# This model runs locally.
#
# No embedding API call is required.
#
# =========================================================

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)