# tools/application_tools.py

import shutil
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool


# =========================================================
# WINDOWS CHECK
# =========================================================

if os.name != "nt":
    raise RuntimeError(
        "application_tools.py only supports Windows."
    )


# =========================================================
# WINDOWS LOCATIONS
# =========================================================

PROGRAM_FILES = os.environ.get(
    "ProgramFiles",
    r"C:\Program Files"
)

PROGRAM_FILES_X86 = os.environ.get(
    "ProgramFiles(x86)",
    r"C:\Program Files (x86)"
)

LOCAL_APP_DATA = os.environ.get(
    "LOCALAPPDATA",
    ""
)

APP_DATA = os.environ.get(
    "APPDATA",
    ""
)

PROGRAM_DATA = os.environ.get(
    "ProgramData",
    r"C:\ProgramData"
)


# =========================================================
# NORMALIZE ONLY FOR COMPARISON
# =========================================================

def normalize_name(name: str) -> str:

    if not name:
        return ""

    name = str(name).strip().lower()

    if name.endswith(".exe"):
        name = name[:-4]

    name = name.replace("_", " ")
    name = name.replace("-", " ")

    name = re.sub(r"\s+", " ", name).strip()

    return name


# =========================================================
# NAME TOKENS
# =========================================================

def name_tokens(name: str):

    normalized = normalize_name(name)

    if not normalized:
        return set()

    return {
        token
        for token in normalized.split()
        if token
    }


# =========================================================
# APPLICATION NAME MATCH
# =========================================================

def application_name_match(
    candidate_name: str,
    requested_name: str
) -> bool:

    candidate = normalize_name(candidate_name)
    requested = normalize_name(requested_name)

    if not candidate or not requested:
        return False

    # Exact match
    if candidate == requested:
        return True

    candidate_tokens = name_tokens(candidate)
    requested_tokens = name_tokens(requested)

    if not requested_tokens:
        return False

    # Every requested word exists in candidate
    return requested_tokens.issubset(candidate_tokens)


# =========================================================
# EXACT NAME MATCH
# =========================================================

def exact_name_match(
    candidate_name: str,
    requested_name: str
) -> bool:

    candidate = normalize_name(candidate_name)
    requested = normalize_name(requested_name)

    return candidate == requested


# =========================================================
# CHECK WHETHER PATH IS A USABLE EXECUTABLE
# =========================================================

def is_usable_executable(path: str) -> bool:

    if not path:
        return False

    if not os.path.isfile(path):
        return False

    return path.lower().endswith(
        (
            ".exe",
            ".cmd",
            ".bat",
            ".com",
        )
    )


# =========================================================
# WINDOWS PATH / CLI SEARCH
# =========================================================

def find_using_where(
    application_name: str
) -> Optional[str]:

    requested = normalize_name(
        application_name
    )

    if not requested:
        return None

    requested_tokens = name_tokens(
        requested
    )

    if not requested_tokens:
        return None

    # -----------------------------------------------------
    # Candidate command names
    # -----------------------------------------------------

    candidates = []

    # Full requested name
    candidates.append(requested)
    candidates.append(requested + ".exe")
    candidates.append(requested + ".cmd")
    candidates.append(requested + ".bat")

    # Individual words
    #
    # Example:
    #
    # Visual Studio Code
    #
    # candidates:
    # visual
    # studio
    # code
    #
    # This allows a CLI called "code" to be discovered.
    # -----------------------------------------------------

    for token in sorted(
        requested_tokens,
        key=len,
        reverse=True
    ):

        candidates.append(token)
        candidates.append(token + ".exe")
        candidates.append(token + ".cmd")
        candidates.append(token + ".bat")

    # Remove duplicates while preserving order
    candidates = list(
        dict.fromkeys(candidates)
    )

    # -----------------------------------------------------
    # Search PATH
    # -----------------------------------------------------

    for candidate in candidates:

        try:

            # shutil.which is faster and handles PATH correctly.
            path = shutil.which(candidate)

            if not path:
                continue

            path = os.path.abspath(path)

            if not is_usable_executable(path):
                continue

            filename = Path(path).stem

            # -------------------------------------------------
            # Exact executable match
            # -------------------------------------------------

            if exact_name_match(
                filename,
                requested
            ):
                return path

            # -------------------------------------------------
            # Normal application-name match
            # -------------------------------------------------

            if application_name_match(
                filename,
                requested
            ):
                return path

            # -------------------------------------------------
            # TOKEN MATCH
            #
            # Example:
            #
            # requested:
            # Visual Studio Code
            #
            # executable:
            # code.cmd
            #
            # "code" is one of the requested tokens.
            # -------------------------------------------------

            executable_tokens = name_tokens(
                filename
            )

            if executable_tokens.intersection(
                requested_tokens
            ):
                return path

        except Exception:
            continue

    return None


# =========================================================
# APP PATHS REGISTRY
# =========================================================

def find_in_app_paths(
    application_name: str
) -> Optional[str]:

    registry_locations = [

        r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",

        r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",

        r"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",

    ]

    requested = normalize_name(
        application_name
    )

    for registry_location in registry_locations:

        try:

            result = subprocess.run(
                [
                    "reg",
                    "query",
                    registry_location
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode != 0:
                continue

            current_keys = []

            for line in result.stdout.splitlines():

                line = line.strip()

                if not line:
                    continue

                if line.startswith("HKEY_"):
                    current_keys.append(line)

            for key in current_keys:

                key_name = key.split("\\")[-1]

                if not application_name_match(
                    key_name,
                    requested
                ):
                    continue

                query = subprocess.run(
                    [
                        "reg",
                        "query",
                        key,
                        "/ve"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                for value_line in query.stdout.splitlines():

                    if "REG_SZ" not in value_line:
                        continue

                    parts = value_line.split(
                        "REG_SZ",
                        1
                    )

                    if len(parts) != 2:
                        continue

                    executable = parts[1].strip()

                    executable = executable.strip('"')

                    # Handle quoted executable paths
                    if (
                        " " in executable
                        and not os.path.isfile(executable)
                    ):

                        possible = executable.split(
                            '"',
                            2
                        )

                        if len(possible) >= 2:
                            executable = possible[1]

                    if is_usable_executable(
                        executable
                    ):

                        return os.path.abspath(
                            executable
                        )

        except Exception:
            continue

    return None


# =========================================================
# WINDOWS REGISTERED START APPS
#
# Supports Microsoft Store / MSIX applications
# =========================================================

def find_in_windows_apps(
    application_name: str
) -> Optional[str]:

    requested = normalize_name(
        application_name
    )

    if not requested:
        return None

    try:

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Get-StartApps | "
                    "Select-Object Name, AppID | "
                    "ConvertTo-Csv -NoTypeInformation"
                )
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            return None

        lines = result.stdout.splitlines()

        for line in lines[1:]:

            # -------------------------------------------------
            # Safer CSV parsing
            # -------------------------------------------------

            parts = line.strip().strip('"').split(
                '","'
            )

            if len(parts) < 2:
                continue

            name = parts[0].strip('"')
            app_id = parts[1].strip('"')

            if application_name_match(
                name,
                requested
            ):

                return (
                    f"shell:AppsFolder\\{app_id}"
                )

    except Exception:
        pass

    return None


# =========================================================
# RESOLVE .LNK
# =========================================================

def resolve_shortcut(
    shortcut_path: str
) -> Optional[str]:

    if not shortcut_path:
        return None

    if not os.path.isfile(shortcut_path):
        return None

    if not shortcut_path.lower().endswith(".lnk"):
        return None

    try:

        escaped = shortcut_path.replace(
            "'",
            "''"
        )

        script = f"""
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut('{escaped}')
$Shortcut.TargetPath
"""

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script
            ],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        target = result.stdout.strip()

        if not target:
            return None

        target = target.strip('"')

        if os.path.isfile(target):

            return os.path.abspath(
                target
            )

    except Exception:
        pass

    return None


# =========================================================
# START MENU SEARCH
# =========================================================

def find_in_start_menu(
    application_name: str
) -> Optional[str]:

    start_menu_locations = [

        os.path.join(
            APP_DATA,
            r"Microsoft\Windows\Start Menu\Programs"
        ),

        os.path.join(
            PROGRAM_DATA,
            r"Microsoft\Windows\Start Menu\Programs"
        ),

    ]

    for start_menu in start_menu_locations:

        if not os.path.isdir(start_menu):
            continue

        try:

            for root, dirs, files in os.walk(
                start_menu
            ):

                for filename in files:

                    full_path = os.path.join(
                        root,
                        filename
                    )

                    stem = Path(filename).stem

                    # -------------------------------------------------
                    # EXE
                    # -------------------------------------------------

                    if filename.lower().endswith(".exe"):

                        if application_name_match(
                            stem,
                            application_name
                        ):

                            return os.path.abspath(
                                full_path
                            )

                    # -------------------------------------------------
                    # LNK
                    # -------------------------------------------------

                    if filename.lower().endswith(".lnk"):

                        if application_name_match(
                            stem,
                            application_name
                        ):

                            target = resolve_shortcut(
                                full_path
                            )

                            if target:
                                return target

        except Exception:
            continue

    return None


# =========================================================
# SEARCH COMMON WINDOWS INSTALLATION LOCATIONS
# =========================================================

def find_in_installation_locations(
    application_name: str
) -> Optional[str]:

    locations = [

        PROGRAM_FILES,

        PROGRAM_FILES_X86,

        os.path.join(
            LOCAL_APP_DATA,
            "Programs"
        ),

    ]

    requested = normalize_name(
        application_name
    )

    requested_tokens = name_tokens(
        requested
    )

    if not requested_tokens:
        return None

    # -----------------------------------------------------
    # Search application folders
    # -----------------------------------------------------

    for base in locations:

        if not os.path.isdir(base):
            continue

        try:

            for folder in os.listdir(base):

                folder_path = os.path.join(
                    base,
                    folder
                )

                if not os.path.isdir(
                    folder_path
                ):
                    continue

                # -------------------------------------------------
                # Flexible folder matching
                # -------------------------------------------------

                if not application_name_match(
                    folder,
                    requested
                ):
                    continue

                executable_candidates = []

                for root, dirs, files in os.walk(
                    folder_path
                ):

                    dirs[:] = [
                        d
                        for d in dirs
                        if d.lower()
                        not in {
                            "node_modules",
                            ".git",
                            "__pycache__",
                            ".venv",
                            "venv",
                            "cache",
                        }
                    ]

                    for filename in files:

                        if not filename.lower().endswith(
                            ".exe"
                        ):
                            continue

                        executable_candidates.append(
                            os.path.join(
                                root,
                                filename
                            )
                        )

                # -------------------------------------------------
                # First prefer executable matching requested name
                # -------------------------------------------------

                for executable in executable_candidates:

                    stem = Path(
                        executable
                    ).stem

                    if application_name_match(
                        stem,
                        requested
                    ):

                        return os.path.abspath(
                            executable
                        )

                # -------------------------------------------------
                # Next prefer executable sharing tokens
                # -------------------------------------------------

                for executable in executable_candidates:

                    stem = normalize_name(
                        Path(executable).stem
                    )

                    executable_tokens = name_tokens(
                        stem
                    )

                    if executable_tokens.intersection(
                        requested_tokens
                    ):

                        return os.path.abspath(
                            executable
                        )

                # -------------------------------------------------
                # Last resort: first executable
                # -------------------------------------------------

                if executable_candidates:

                    return os.path.abspath(
                        executable_candidates[0]
                    )

        except Exception:
            continue

    return None


# =========================================================
# DIRECT USER PATH
# =========================================================

def check_direct_path(
    application_name: str
) -> Optional[str]:

    value = application_name.strip().strip('"')

    if os.path.isfile(value):

        if value.lower().endswith(
            (
                ".exe",
                ".cmd",
                ".bat",
                ".com",
            )
        ):

            return os.path.abspath(
                value
            )

    return None


# =========================================================
# MAIN DISCOVERY
#
# Order:
#
# 1. Exact user path
# 2. Windows App Paths
# 3. PATH / CLI
# 4. Start Menu
# 5. Windows registered apps
# 6. Installation directories
#
# PATH is intentionally before Windows registered apps.
# This allows applications with CLI launchers to receive
# files/folders as command-line arguments.
# =========================================================

def find_application(
    application_name: str
) -> Optional[str]:

    if not application_name:
        return None

    # -----------------------------------------------------
    # 1. Direct user path
    # -----------------------------------------------------

    result = check_direct_path(
        application_name
    )

    if result:
        return result

    # -----------------------------------------------------
    # 2. Windows App Paths
    # -----------------------------------------------------

    result = find_in_app_paths(
        application_name
    )

    if result:
        return result

    # -----------------------------------------------------
    # 3. PATH / CLI
    # -----------------------------------------------------

    result = find_using_where(
        application_name
    )

    if result:
        return result

    # -----------------------------------------------------
    # 4. Start Menu
    # -----------------------------------------------------

    result = find_in_start_menu(
        application_name
    )

    if result:
        return result

    # -----------------------------------------------------
    # 5. Windows registered apps
    # -----------------------------------------------------

    result = find_in_windows_apps(
        application_name
    )

    if result:
        return result

    # -----------------------------------------------------
    # 6. Installation directories
    # -----------------------------------------------------

    result = find_in_installation_locations(
        application_name
    )

    if result:
        return result

    return None


# =========================================================
# LAUNCH APPLICATION
# =========================================================

def launch_application(
    executable,
    arguments=None
):

    """
    Launch an application with optional arguments.

    Supports:

    - .exe
    - .cmd
    - .bat
    - .com
    - Windows shell/MSIX applications

    Arguments are passed directly to the application.
    """

    arguments = arguments or []

    try:

        # =================================================
        # WINDOWS SHELL / MSIX APPLICATION
        # =================================================

        if executable.lower().startswith(
            "shell:"
        ):

            # Try to find a CLI launcher using the
            # application identifier.

            shell_name = executable.split(
                "\\"
            )[-1]

            cli_candidates = [

                shell_name,

                shell_name.split(".")[-1],

            ]

            # -------------------------------------------------
            # Try every candidate
            # -------------------------------------------------

            for candidate in cli_candidates:

                cli_path = shutil.which(
                    candidate
                )

                if not cli_path:
                    continue

                cli_path = os.path.abspath(
                    cli_path
                )

                if cli_path.lower().endswith(
                    (
                        ".cmd",
                        ".bat"
                    )
                ):

                    subprocess.Popen(
                        [
                            "cmd.exe",
                            "/c",
                            cli_path,
                            *arguments
                        ],
                        shell=False
                    )

                else:

                    subprocess.Popen(
                        [
                            cli_path,
                            *arguments
                        ],
                        shell=False
                    )

                return True

            # -------------------------------------------------
            # No CLI found.
            #
            # Open the shell application normally.
            # -------------------------------------------------

            subprocess.Popen(
                [
                    "explorer.exe",
                    executable
                ],
                shell=False
            )

            return True

        # =================================================
        # NORMAL EXECUTABLE
        # =================================================

        if not is_usable_executable(
            executable
        ):

            return False

        # -------------------------------------------------
        # CMD / BAT
        # -------------------------------------------------

        if executable.lower().endswith(
            (
                ".cmd",
                ".bat"
            )
        ):

            subprocess.Popen(
                [
                    "cmd.exe",
                    "/c",
                    executable,
                    *arguments
                ],
                shell=False
            )

        # -------------------------------------------------
        # EXE / COM
        # -------------------------------------------------

        else:

            subprocess.Popen(
                [
                    executable,
                    *arguments
                ],
                shell=False
            )

        return True

    except Exception as e:

        print(
            f"Error launching application: {e}"
        )

        return False


# =========================================================
# OPEN APPLICATION
# =========================================================

@tool
def open_application(
    application_name: str
) -> str:

    """
    Find and open any installed Windows application.
    """

    try:

        path = find_application(
            application_name
        )

        if not path:

            return (
                f"Application not found: "
                f"{application_name}"
            )

        success = launch_application(
            path
        )

        if not success:

            return (
                f"Could not open "
                f"{application_name}."
            )

        return (
            f"{application_name} opened."
        )

    except Exception as e:

        return (
            f"Failed to open application: {e}"
        )


# =========================================================
# CLOSE APPLICATION
# =========================================================

@tool
def close_application(
    application_name: str
) -> str:

    """
    Close an installed Windows application.
    """

    try:

        path = find_application(
            application_name
        )

        if not path:

            return (
                f"Application not found: "
                f"{application_name}"
            )

        # -------------------------------------------------
        # Shell application
        # -------------------------------------------------

        if path.lower().startswith(
            "shell:appsfolder\\"
        ):

            return (
                f"Could not determine process name "
                f"for {application_name}."
            )

        # -------------------------------------------------
        # Normal executable / launcher
        # -------------------------------------------------

        process_name = os.path.basename(
            path
        )

        # For CLI launchers such as .cmd/.bat,
        # remove the launcher extension and try to
        # find the actual running process.

        if process_name.lower().endswith(
            (
                ".cmd",
                ".bat"
            )
        ):

            process_name = (
                Path(process_name).stem
                + ".exe"
            )

        result = subprocess.run(
            [
                "taskkill",
                "/IM",
                process_name,
                "/T",
                "/F"
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode == 0:

            return (
                f"{application_name} closed."
            )

        return (
            f"Could not close "
            f"{application_name}."
        )

    except Exception as e:

        return (
            f"Failed to close application: {e}"
        )


# =========================================================
# OPEN FILE WITH APPLICATION
# =========================================================

@tool
def open_file_with_application(
    file_path: str,
    application_name: str
) -> str:

    """
    Open a file using any dynamically discovered
    Windows application.
    """

    try:

        if not os.path.isfile(
            file_path
        ):

            return (
                f"File not found: "
                f"{file_path}"
            )

        file_path = os.path.abspath(
            file_path
        )

        application_path = find_application(
            application_name
        )

        if not application_path:

            return (
                f"Application not found: "
                f"{application_name}"
            )

        success = launch_application(
            application_path,
            [
                file_path
            ]
        )

        if not success:

            return (
                f"Could not open file "
                f"with {application_name}."
            )

        return (
            f"File opened in "
            f"{application_name}."
        )

    except Exception as e:

        return (
            f"Failed to open file: "
            f"{e}"
        )


# =========================================================
# OPEN FOLDER WITH APPLICATION
# =========================================================

@tool
def open_folder_with_application(
    folder_path: str,
    application_name: str
) -> str:

    """
    Open a folder/workspace using any dynamically
    discovered Windows application.
    """

    try:

        if not os.path.isdir(
            folder_path
        ):

            return (
                f"Folder not found: "
                f"{folder_path}"
            )

        folder_path = os.path.abspath(
            folder_path
        )

        application_path = find_application(
            application_name
        )

        if not application_path:

            return (
                f"Application not found: "
                f"{application_name}"
            )

        success = launch_application(
            application_path,
            [
                folder_path
            ]
        )

        if not success:

            return (
                f"Could not open folder "
                f"in {application_name}."
            )

        return (
            f"Folder opened in "
            f"{application_name}."
        )

    except Exception as e:

        return (
            f"Failed to open folder in "
            f"{application_name}: {e}"
        )


# =========================================================
# FIND APPLICATION PATH
# =========================================================

@tool
def find_application_path(
    application_name: str
) -> str:

    """
    Find the executable or launcher Windows uses
    for an application.
    """

    try:

        path = find_application(
            application_name
        )

        if not path:

            return (
                f"Application not found: "
                f"{application_name}"
            )

        return (
            f"Application: {application_name}\n"
            f"Executable: {path}"
        )

    except Exception as e:

        return (
            f"Failed to find application: "
            f"{e}"
        )