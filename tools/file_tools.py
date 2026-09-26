import os
import shutil
import string

from langchain_core.tools import tool


# =========================================================
# CONFIGURATION
# =========================================================

# Maximum number of file paths returned to the LLM.
# The search still scans all available drives and counts
# all matches. Only the returned context is limited.
MAX_SEARCH_RESULTS = 50


# =========================================================
# SEARCH FILE
# =========================================================

@tool
def search_file(filename: str) -> str:
    """
    Search for a file across all available drives.

    Use for filename or extension searches.
    """

    filename = filename.strip().lower()

    if not filename:
        return "Please provide a filename or file pattern."

    # -----------------------------------------------------
    # FIND ALL AVAILABLE WINDOWS DRIVES
    # -----------------------------------------------------

    drives = []

    for drive_letter in string.ascii_uppercase:

        drive = f"{drive_letter}:\\"

        if os.path.exists(drive):
            drives.append(drive)

    if not drives:
        return "No drives were found."

    # -----------------------------------------------------
    # DIRECTORIES TO SKIP
    # -----------------------------------------------------

    skip_directories = {
        "$recycle.bin",
        "system volume information",
        "windows",
        "program files",
        "program files (x86)",
        "programdata",
        "appdata",
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".cache",
        "cache",
    }

    matches = []

    # -----------------------------------------------------
    # SEARCH ALL DRIVES
    # -----------------------------------------------------

    for drive in drives:

        try:

            for root, dirs, files in os.walk(
                drive,
                topdown=True,
            ):

                # Skip unwanted directories
                dirs[:] = [
                    directory
                    for directory in dirs
                    if directory.lower()
                    not in skip_directories
                ]

                # -------------------------------------------------
                # SEARCH FILES
                # -------------------------------------------------

                for file in files:

                    file_lower = file.lower()

                    # ---------------------------------------------
                    # Extension search
                    # Example: *.py
                    # ---------------------------------------------

                    if filename.startswith("*."):

                        extension = filename[1:]

                        if file_lower.endswith(extension):

                            matches.append(
                                os.path.join(
                                    root,
                                    file,
                                )
                            )

                    # ---------------------------------------------
                    # Filename / partial search
                    # ---------------------------------------------

                    elif filename in file_lower:

                        matches.append(
                            os.path.join(
                                root,
                                file,
                            )
                        )

        except (PermissionError, OSError):

            # Skip locations Windows does not allow access to.
            continue

    # -----------------------------------------------------
    # REMOVE DUPLICATES
    # -----------------------------------------------------

    matches = list(
        dict.fromkeys(matches)
    )

    # -----------------------------------------------------
    # NO RESULTS
    # -----------------------------------------------------

    if not matches:

        return (
            f"No file found matching "
            f"'{filename}' on the available drives."
        )

    # -----------------------------------------------------
    # LIMIT LLM OUTPUT
    # -----------------------------------------------------

    total_matches = len(matches)

    results = matches[:MAX_SEARCH_RESULTS]

    # -----------------------------------------------------
    # BUILD RESPONSE
    # -----------------------------------------------------

    output = "\n".join(results)

    if total_matches > MAX_SEARCH_RESULTS:

        output += (
            f"\n\nShowing first {MAX_SEARCH_RESULTS} "
            f"results out of {total_matches} matches."
        )

    else:

        output += (
            f"\n\nTotal matches: "
            f"{total_matches}"
        )

    return output


# =========================================================
# GET FILE
# =========================================================

@tool
def get_file(filepath: str) -> str:
    """
    Locate and return an existing file to give, attach, or show it in the chat.
    Use this whenever the user asks to 'give', 'get', 'show', 'fetch', or find a file.
    """

    filepath = os.path.expandvars(
        os.path.expanduser(filepath)
    )

    if not os.path.isfile(filepath):
        return (
            f"File not found: "
            f"{filepath}"
        )

    filename = os.path.basename(filepath)
    normalized = filepath.replace("\\", "/")
    lower = filename.lower()
    if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
        return f"File found: {filepath}. Markdown: ![{filename}]({normalized})"

    return f"File found: {filepath}. Markdown: [{filename}]({normalized})"


# =========================================================
# READ FILE (ONLY WHEN EXPLICITLY ASKED FOR CONTENTS)
# =========================================================

@tool
def read_file(filepath: str) -> str:
    """
    Read and return the text content written inside a file.
    ONLY use this tool when the user explicitly asks to READ, inspect, or see the text/code content INSIDE a file
    (e.g., 'what is written in good.txt', 'read good.txt', 'show me the contents of the file').
    Do NOT use this tool when the user simply asks to 'give' or 'show' the file itself; use get_file instead.
    """

    filepath = os.path.expandvars(
        os.path.expanduser(filepath)
    )

    if not os.path.isfile(filepath):
        return (
            f"File not found: "
            f"{filepath}"
        )

    lower = filepath.lower()
    if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
        normalized = filepath.replace("\\", "/")
        return f"Image file: ![{os.path.basename(filepath)}]({normalized})"

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as file:
            content = file.read(50000)
            if len(content) >= 50000:
                content += "\n... [Content truncated at 50,000 characters]"
            return content
    except Exception as e:
        return f"Failed to read file: {e}"


# =========================================================
# OPEN FILE (ON OPERATING SYSTEM)
# =========================================================

@tool
def open_file(filepath: str) -> str:
    """
    Open a file using the default Windows application on the desktop.
    CRITICAL: ONLY use this tool when the user explicitly requests to 'open' a file.
    NEVER use this tool if the user says 'show', 'give', 'display', or 'view'.
    """

    filepath = os.path.expandvars(
        os.path.expanduser(filepath)
    )

    if not os.path.isfile(filepath):

        return (
            f"File not found: "
            f"{filepath}"
        )

    try:

        os.startfile(filepath)

        return (
            f"Opened file successfully: "
            f"{filepath}"
        )

    except Exception as e:

        return (
            f"Failed to open file: "
            f"{e}"
        )


# =========================================================
# WRITE FILE
# =========================================================

@tool
def write_file(
    filepath: str,
    content: str,
) -> str:
    """
    Write content to a file.
    Creates the file if it doesn't exist.
    """

    filepath = os.path.expandvars(
        os.path.expanduser(filepath)
    )

    try:

        parent = os.path.dirname(filepath)

        if parent and not os.path.exists(parent):

            os.makedirs(parent)

        with open(
            filepath,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(content)

        return (
            f"File written successfully: "
            f"{filepath}"
        )

    except Exception as e:

        return (
            f"Failed to write file: "
            f"{e}"
        )


# =========================================================
# MOVE FILE
# =========================================================

@tool
def move_file(
    file_path: str,
    destination_folder: str,
) -> str:
    """
    Move a FILE to another folder.
    """

    file_path = os.path.expandvars(
        os.path.expanduser(file_path)
    )

    destination_folder = os.path.expandvars(
        os.path.expanduser(destination_folder)
    )

    if not os.path.isfile(file_path):

        return (
            f"File not found: "
            f"{file_path}"
        )

    if not os.path.isdir(destination_folder):

        return (
            f"Destination folder not found: "
            f"{destination_folder}"
        )

    try:

        destination = os.path.join(
            destination_folder,
            os.path.basename(file_path),
        )

        shutil.move(
            file_path,
            destination,
        )

        return (
            f"File moved successfully to: "
            f"{destination}"
        )

    except Exception as e:

        return (
            f"Failed to move file: "
            f"{e}"
        )


# =========================================================
# COPY FILE
# =========================================================

@tool
def copy_file(
    file_path: str,
    destination_folder: str,
) -> str:
    """
    Copy a FILE to another folder.
    """

    file_path = os.path.expandvars(
        os.path.expanduser(file_path)
    )

    destination_folder = os.path.expandvars(
        os.path.expanduser(destination_folder)
    )

    if not os.path.isfile(file_path):

        return (
            f"File not found: "
            f"{file_path}"
        )

    if not os.path.isdir(destination_folder):

        return (
            f"Destination folder not found: "
            f"{destination_folder}"
        )

    try:

        destination = os.path.join(
            destination_folder,
            os.path.basename(file_path),
        )

        shutil.copy2(
            file_path,
            destination,
        )

        return (
            f"File copied successfully to: "
            f"{destination}"
        )

    except Exception as e:

        return (
            f"Failed to copy file: "
            f"{e}"
        )