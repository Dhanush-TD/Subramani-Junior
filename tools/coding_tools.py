import os
import subprocess

from langchain_core.tools import tool


OPENCODE_PATH = r"C:\Users\dhanu\AppData\Roaming\npm\opencode.cmd"


@tool
def coding_tool(task: str, workspace: str):
    """
    Use the dedicated OpenCode coding agent for software-engineering tasks.

    Use this tool ONLY for:
    - writing code
    - creating code
    - modifying code
    - debugging code
    - fixing errors
    - implementing features
    - refactoring
    - testing code
    - building software projects

    OpenCode uses its own specialized coding LLM.
    """

    if not task or not task.strip():
        return "Coding task was not provided."

    if not workspace or not os.path.isdir(workspace):
        return f"Invalid coding workspace: {workspace}"

    try:
        result = subprocess.run(
            [
                OPENCODE_PATH,
                "run",
                "--dir",
                workspace,
                task,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=workspace,
        )

        output = result.stdout or ""
        error = result.stderr or ""

        output = output.strip()
        error = error.strip()

        if result.returncode != 0:
            return (
                f"OpenCode failed with exit code {result.returncode}.\n\n"
                f"STDOUT:\n{output}\n\n"
                f"STDERR:\n{error}"
            )

        return (
            "OpenCode completed the coding task successfully.\n\n"
            f"{output}"
        )

    except Exception as e:
        return f"Could not run OpenCode: {e}"