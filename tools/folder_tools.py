
import os
import shutil
import string

from langchain_core.tools import tool


# =========================================================
# SEARCH FOLDER
# =========================================================

@tool
def search_folder(folder_name: str):
    """
    Search for a folder across all available drives.

    Examples:
    - local-file-agent
    - project
    - downloads
    - python
    """

    folder_name = folder_name.strip().lower()

    if not folder_name:
        return "Please provide a folder name."

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
                topdown=True
            ):

                # Skip unwanted directories
                dirs[:] = [
                    directory
                    for directory in dirs
                    if directory.lower()
                    not in skip_directories
                ]

                # Search folders
                for directory in dirs:

                    if folder_name in directory.lower():

                        matches.append(
                            os.path.join(
                                root,
                                directory
                            )
                        )

        except (PermissionError, OSError):

            # Skip locations Windows does not allow access to
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
            f"No folder found matching "
            f"'{folder_name}' on the available drives."
        )

    # -----------------------------------------------------
    # LIMIT RESULTS
    # -----------------------------------------------------

    max_results = 100

    total_matches = len(matches)

    results = matches[:max_results]

    # -----------------------------------------------------
    # RETURN RESULTS
    # -----------------------------------------------------

    output = "\n".join(results)

    if total_matches > max_results:

        output += (
            f"\n\nShowing first {max_results} "
            f"results out of {total_matches} matches."
        )

    else:

        output += (
            f"\n\nTotal matches: "
            f"{total_matches}"
        )

    return output


# =========================================================
# OPEN FOLDER
# =========================================================

@tool
def open_folder(folder_path: str):
    """
    Open a folder in Windows File Explorer.
    """

    folder_path = os.path.expandvars(
        os.path.expanduser(folder_path)
    )

    if not os.path.isdir(folder_path):

        return (
            f"Folder not found: "
            f"{folder_path}"
        )

    try:

        os.startfile(folder_path)

        return (
            f"Opened folder successfully: "
            f"{folder_path}"
        )

    except Exception as e:

        return (
            f"Failed to open folder: "
            f"{e}"
        )


# =========================================================
# MOVE FOLDER
# =========================================================

@tool
def move_folder(
    folder_path: str,
    destination_folder: str
):
    """
    Move a FOLDER to another folder.
    """

    folder_path = os.path.expandvars(
        os.path.expanduser(folder_path)
    )

    destination_folder = os.path.expandvars(
        os.path.expanduser(destination_folder)
    )

    if not os.path.isdir(folder_path):

        return (
            f"Folder not found: "
            f"{folder_path}"
        )

    if not os.path.isdir(destination_folder):

        return (
            f"Destination folder not found: "
            f"{destination_folder}"
        )

    try:

        destination = os.path.join(
            destination_folder,
            os.path.basename(folder_path)
        )

        shutil.move(
            folder_path,
            destination
        )

        return (
            f"Folder moved successfully to: "
            f"{destination}"
        )

    except Exception as e:

        return (
            f"Failed to move folder: "
            f"{e}"
        )


# =========================================================
# COPY FOLDER
# =========================================================

@tool
def copy_folder(
    folder_path: str,
    destination_folder: str
):
    """
    Copy a FOLDER to another folder.
    """

    folder_path = os.path.expandvars(
        os.path.expanduser(folder_path)
    )

    destination_folder = os.path.expandvars(
        os.path.expanduser(destination_folder)
    )

    if not os.path.isdir(folder_path):

        return (
            f"Folder not found: "
            f"{folder_path}"
        )

    if not os.path.isdir(destination_folder):

        return (
            f"Destination folder not found: "
            f"{destination_folder}"
        )

    try:

        destination = os.path.join(
            destination_folder,
            os.path.basename(folder_path)
        )

        shutil.copytree(
            folder_path,
            destination
        )

        return (
            f"Folder copied successfully to: "
            f"{destination}"
        )

    except Exception as e:

        return (
            f"Failed to copy folder: "
            f"{e}"
        )
