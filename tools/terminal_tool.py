import os
import shlex
import subprocess
from typing import Optional

from langchain_core.tools import tool


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120

# Maximum amount of command output returned to the LLM.
# This prevents large terminal output from consuming
# unnecessary DeepSeek tokens.
MAX_OUTPUT_CHARS = 8000


# =========================================================
# ALLOWED COMMANDS
# =========================================================

ALLOWED_COMMANDS = {
    # Python / package
    "python",
    "pip",

    # File / folder
    "dir",
    "cd",
    "mkdir",
    "type",
    "copy",
    "move",

    # Network
    "ipconfig",
    "ping",

    # Processes
    "tasklist",

    # Git
    "git",

    # Deletion
    "del",
    "erase",
    "rmdir",
    "rd",
    "remove-item",
}


# =========================================================
# READ-ONLY COMMANDS
# =========================================================

READ_COMMANDS = {
    "python",
    "pip",
    "dir",
    "cd",
    "type",
    "ipconfig",
    "ping",
    "tasklist",
    "git",
}


# =========================================================
# MODIFYING COMMANDS
# =========================================================

MODIFY_COMMANDS = {
    "mkdir",
    "copy",
    "move",
}


# =========================================================
# DELETE COMMANDS
# =========================================================

DELETE_COMMANDS = {
    "del",
    "erase",
    "rmdir",
    "rd",
    "remove-item",
}


# =========================================================
# BLOCKED POWERSHELL OPERATORS
# =========================================================

BLOCKED_OPERATORS = {
    "&&",
    "||",
    ";",
    "|",
    ">",
    ">>",
    "<",
}


# =========================================================
# TRUNCATE OUTPUT
# =========================================================

def _truncate_output(
    output: str,
    max_chars: int = MAX_OUTPUT_CHARS,
) -> str:
    """
    Limit terminal output returned to the LLM.

    Keeps the beginning and end of large output so that
    useful information is less likely to be lost.
    """

    if not output:
        return ""

    if len(output) <= max_chars:
        return output

    # Keep useful information from both ends.
    head_size = max_chars // 2
    tail_size = max_chars - head_size

    return (
        output[:head_size]
        + "\n\n"
        "[OUTPUT TRUNCATED FOR TOKEN EFFICIENCY]\n"
        "[Original output was larger than the allowed limit]\n\n"
        + output[-tail_size:]
    )


# =========================================================
# GET COMMAND NAME
# =========================================================

def _get_command_name(command: str) -> str:
    """
    Extract the first command name.
    """

    try:
        parts = shlex.split(command, posix=False)
    except ValueError:
        return ""

    if not parts:
        return ""

    name = parts[0].strip().lower()

    # Remove surrounding quotes
    name = name.strip('"').strip("'")

    # Remove .exe
    if name.endswith(".exe"):
        name = name[:-4]

    return name


# =========================================================
# CHECK COMMAND OPERATORS
# =========================================================

def _contains_blocked_operator(
    command: str,
) -> Optional[str]:
    """
    Detect blocked command chaining/redirection operators.
    """

    for operator in BLOCKED_OPERATORS:

        if operator in command:
            return operator

    return None


# =========================================================
# VALIDATE COMMAND
# =========================================================

def _validate_command(
    command: str,
) -> tuple[bool, str]:

    if not command or not command.strip():
        return False, "ERROR: Command cannot be empty."

    command = command.strip()

    # -----------------------------------------------------
    # Block command chaining
    # -----------------------------------------------------

    blocked = _contains_blocked_operator(command)

    if blocked:

        return (
            False,
            f"ERROR: Operator '{blocked}' is not allowed.",
        )

    # -----------------------------------------------------
    # Get command name
    # -----------------------------------------------------

    command_name = _get_command_name(command)

    if not command_name:

        return (
            False,
            "ERROR: Could not understand the command.",
        )

    # -----------------------------------------------------
    # Check allowlist
    # -----------------------------------------------------

    if command_name not in ALLOWED_COMMANDS:

        return (
            False,
            f"ERROR: Command '{command_name}' is not allowed.\n\n"
            f"Allowed commands:\n"
            f"{', '.join(sorted(ALLOWED_COMMANDS))}",
        )

    return True, command_name


# =========================================================
# CONFIRMATION REQUIRED?
# =========================================================

def _requires_confirmation(command: str) -> bool:

    command_name = _get_command_name(command)

    # Delete
    if command_name in DELETE_COMMANDS:
        return True

    # Move
    if command_name == "move":
        return True

    # Copy
    if command_name == "copy":
        return True

    return False


# =========================================================
# BUILD CONFIRMATION MESSAGE
# =========================================================

def _get_confirmation_message(
    command: str,
) -> str:

    command_name = _get_command_name(command)

    if command_name in DELETE_COMMANDS:

        return (
            "CONFIRMATION_REQUIRED\n\n"
            "This command can permanently delete "
            "files or folders:\n\n"
            f"{command}\n\n"
            "Ask the user for explicit confirmation "
            "before executing it."
        )

    if command_name == "move":

        return (
            "CONFIRMATION_REQUIRED\n\n"
            "This command will move files or folders:\n\n"
            f"{command}\n\n"
            "Ask the user for explicit confirmation "
            "before executing it."
        )

    if command_name == "copy":

        return (
            "CONFIRMATION_REQUIRED\n\n"
            "This command will create/copy files or folders "
            "and may overwrite an existing destination:\n\n"
            f"{command}\n\n"
            "Ask the user for explicit confirmation "
            "before executing it."
        )

    return ""


# =========================================================
# EXECUTE POWERSHELL
# =========================================================

def _execute_powershell(
    command: str,
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
) -> str:

    # -----------------------------------------------------
    # Validate timeout
    # -----------------------------------------------------

    if timeout <= 0:
        return "ERROR: Timeout must be greater than 0."

    timeout = min(timeout, MAX_TIMEOUT)

    # -----------------------------------------------------
    # Validate cwd
    # -----------------------------------------------------

    if cwd:

        cwd = os.path.abspath(cwd)

        if not os.path.isdir(cwd):

            return (
                "ERROR: Working directory does not exist:\n"
                f"{cwd}"
            )

    # -----------------------------------------------------
    # Execute PowerShell
    # -----------------------------------------------------

    try:

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        if result.returncode == 0:

            if stdout:
                return _truncate_output(stdout)

            return "Command executed successfully."

        # -------------------------------------------------
        # FAILURE
        # -------------------------------------------------

        output_parts = [
            f"Command failed with exit code {result.returncode}"
        ]

        if stdout:

            output_parts.append(
                "STDOUT:\n"
                + _truncate_output(stdout)
            )

        if stderr:

            output_parts.append(
                "STDERR:\n"
                + _truncate_output(stderr)
            )

        return "\n\n".join(output_parts)

    # -----------------------------------------------------
    # TIMEOUT
    # -----------------------------------------------------

    except subprocess.TimeoutExpired:

        return (
            f"ERROR: Command timed out after "
            f"{timeout} seconds."
        )

    # -----------------------------------------------------
    # OTHER ERROR
    # -----------------------------------------------------

    except Exception as e:

        return (
            f"ERROR: {type(e).__name__}: {e}"
        )


# =========================================================
# CONFIRMED EXECUTION
# =========================================================

def execute_confirmed_terminal_command(
    command: str,
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
) -> str:
    """
    Execute a command ONLY after the user has explicitly
    confirmed the operation.
    """

    valid, result = _validate_command(command)

    if not valid:
        return result

    # -----------------------------------------------------
    # Make sure this requires confirmation
    # -----------------------------------------------------

    if not _requires_confirmation(command):

        return (
            "ERROR: This function is only for commands "
            "that require confirmation."
        )

    print(
        f"[TERMINAL] Executing confirmed command: "
        f"{command}"
    )

    return _execute_powershell(
        command=command,
        timeout=timeout,
        cwd=cwd,
    )


# =========================================================
# MAIN TERMINAL TOOL
# =========================================================

@tool
def terminal_tool(
    command: str,
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
) -> str:
    """
    Execute an approved Windows PowerShell command.

    Read-only commands execute immediately.

    File/folder modifications and deletion require
    explicit user confirmation.
    """

    command = command.strip()

    # -----------------------------------------------------
    # VALIDATE
    # -----------------------------------------------------

    valid, result = _validate_command(command)

    if not valid:
        return result

    # -----------------------------------------------------
    # CONFIRMATION REQUIRED
    # -----------------------------------------------------

    if _requires_confirmation(command):

        return _get_confirmation_message(command)

    # -----------------------------------------------------
    # READ-ONLY / SAFE COMMAND
    # -----------------------------------------------------

    print(
        f"[TERMINAL] Executing: {command}"
    )

    return _execute_powershell(
        command=command,
        timeout=timeout,
        cwd=cwd,
    )


# =========================================================
# OPTIONAL: COMMAND INFORMATION
# =========================================================

def get_terminal_command_info(
    command: str,
) -> dict:

    command_name = _get_command_name(command)

    if not command_name:

        return {
            "valid": False,
            "command": "",
            "requires_confirmation": False,
        }

    valid, result = _validate_command(command)

    return {
        "valid": valid,
        "command": command_name,
        "requires_confirmation": (
            _requires_confirmation(command)
            if valid
            else False
        ),
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print(" Terminal Tool Test")
    print("======================================")
    print()

    tests = [
        "python --version",
        "pip --version",
        "dir",
        "ipconfig",
        "tasklist",
        "git status",
        "mkdir test_folder",
        "copy test.txt test2.txt",
        "move test.txt test2.txt",
        "del test.txt",
        "rmdir test_folder",
        "Remove-Item test.txt",
        "python --version; whoami",
        "python --version | whoami",
    ]

    for command in tests:

        print("--------------------------------------")
        print(f"COMMAND: {command}")

        info = get_terminal_command_info(command)

        print(f"INFO: {info}")

        result = terminal_tool.invoke({
            "command": command
        })

        print(f"RESULT:\n{result}")

        print()