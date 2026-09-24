import os

from pathlib import Path

from .config import (
    INDEX_DIRECTORIES,
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
)


# =========================================================
# CHECK WHETHER FILE IS SUPPORTED
# =========================================================

def is_supported_file(
    file_path: str
) -> bool:

    path = Path(
        file_path
    )

    # -----------------------------------------------------
    # CHECK EXTENSION
    # -----------------------------------------------------

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:

        return False

    # -----------------------------------------------------
    # CHECK FILE SIZE
    # -----------------------------------------------------

    try:

        size_mb = (
            os.path.getsize(
                file_path
            )
            /
            (1024 * 1024)
        )

        if size_mb > MAX_FILE_SIZE_MB:

            print(
                f"[RAG] Skipping large file: "
                f"{file_path}"
            )

            return False

    except OSError:

        return False

    return True


# =========================================================
# SCAN FILES
# =========================================================

def scan_files():

    """
    Recursively scan all configured directories.

    Yields supported file paths.
    """

    for directory in INDEX_DIRECTORIES:

        directory = os.path.abspath(
            os.path.expanduser(
                directory
            )
        )

        # -------------------------------------------------
        # DIRECTORY DOES NOT EXIST
        # -------------------------------------------------

        if not os.path.isdir(
            directory
        ):

            print(
                f"[RAG] Directory not found: "
                f"{directory}"
            )

            continue

        print(
            f"[RAG] Scanning: {directory}"
        )

        # -------------------------------------------------
        # WALK DIRECTORY
        # -------------------------------------------------

        for root, dirs, files in os.walk(
            directory
        ):

            # -------------------------------------------------
            # SKIP UNNECESSARY DIRECTORIES
            # -------------------------------------------------

            dirs[:] = [

                directory_name

                for directory_name in dirs

                if directory_name.lower()
                not in {

                    ".git",

                    "__pycache__",

                    "node_modules",

                    ".venv",

                    "venv",

                    "env",

                    ".idea",

                    ".vscode",

                    "rag_data",

                }

            ]

            # -------------------------------------------------
            # PROCESS FILES
            # -------------------------------------------------

            for filename in files:

                file_path = os.path.join(
                    root,
                    filename
                )

                if is_supported_file(
                    file_path
                ):

                    yield os.path.abspath(
                        file_path
                    )


# =========================================================
# READ FILE
# =========================================================

def read_file(
    file_path: str
):

    """
    Read a text file safely.
    """

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            return file.read()

    except Exception as e:

        print(
            f"[RAG] Could not read file:"
        )

        print(
            f"       {file_path}"
        )

        print(
            f"       {e}"
        )

        return None