import os
import shutil
import traceback
import asyncio
from datetime import datetime

from dotenv import load_dotenv

from browser_use import Agent, BrowserSession
from browser_use.llm import ChatOpenAI

from langchain_core.tools import tool


load_dotenv()


# =========================================================
# SCREENSHOT DIRECTORY
# =========================================================

PROJECT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

SCREENSHOT_DIR = os.path.join(
    PROJECT_DIR,
    "screenshots"
)

os.makedirs(
    SCREENSHOT_DIR,
    exist_ok=True
)


# =========================================================
# ASYNC BROWSER TASK
# =========================================================

async def _browser_task_async(task: str) -> str:
    """
    Start Browser Use only for this request.

    Browser lifecycle:

        create BrowserSession
              ↓
        create Agent
              ↓
        agent.run()
              ↓
        get result / screenshot
              ↓
        browser_session.kill()
              ↓
        browser completely stopped
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return "Error: OPENAI_API_KEY is not configured."

    browser_session = None

    try:

        print("\n========================================")
        print("Starting Browser Use")
        print("========================================")

        # =================================================
        # DETECT SCREENSHOT REQUEST
        # =================================================

        task_lower = task.lower()

        screenshot_requested = any(
            phrase in task_lower
            for phrase in [
                "screenshot",
                "screen shot",
                "capture the page",
                "capture this page",
                "take a picture of the page",
            ]
        )

        # =================================================
        # BROWSER INSTRUCTIONS
        # =================================================

        if screenshot_requested:

            browser_instructions = f"""
You are controlling a real browser.

Complete this task:

{task}

SCREENSHOT REQUIREMENTS:

The user requested a webpage screenshot.

You MUST:

1. Navigate to the requested website.
2. Find the exact requested page.
3. Verify the correct webpage is visible.
4. Take the screenshot using the browser screenshot action.
5. Do not take a Windows desktop screenshot.
6. Do not take a terminal screenshot.
7. Take the screenshot before completing the task.
8. Do not mark the task complete until all requested actions
   and the screenshot are completed.
"""

        else:

            browser_instructions = f"""
You are controlling a real browser.

Complete this task:

{task}

Complete all requested browser actions before marking
the task as done.
"""

        # =================================================
        # LUNA
        # =================================================

        llm = ChatOpenAI(
            model="gpt-5.6-luna",
            api_key=api_key,
            reasoning_effort="low",
        )

        # =================================================
        # CREATE A NEW BROWSER SESSION
        # =================================================
        #
        # IMPORTANT:
        # A NEW session is created for THIS browser task only.
        #
        # It is not stored globally.
        # It is not reused by the rest of your agent.
        # =================================================

        browser_session = BrowserSession(
            headless=False
        )

        print("[Browser] Session created.")

        # =================================================
        # CREATE BROWSER AGENT
        # =================================================

        agent = Agent(
            task=browser_instructions,
            llm=llm,
            use_vision=True,
            browser_session=browser_session,
        )

        # =================================================
        # RUN BROWSER TASK
        # =================================================

        print("[Browser] Running task...")

        history = await agent.run()

        print("[Browser] Task finished.")

        # =================================================
        # SCREENSHOT PATHS
        # =================================================

        try:
            screenshot_paths = history.screenshot_paths()
        except Exception:
            screenshot_paths = []

        # =================================================
        # SCREENSHOT REQUESTED
        # =================================================

        if screenshot_requested:

            if not screenshot_paths:

                return (
                    "Browser task completed, "
                    "but no browser screenshot was found."
                )

            # -------------------------------------------------
            # Latest screenshot
            # -------------------------------------------------

            source_screenshot = screenshot_paths[-1]

            print(
                f"[Browser] Screenshot source:\n"
                f"{source_screenshot}"
            )

            # -------------------------------------------------
            # Verify source screenshot
            # -------------------------------------------------

            if not os.path.isfile(source_screenshot):

                return (
                    "Browser task completed, "
                    "but the screenshot file "
                    "could not be found."
                )

            # -------------------------------------------------
            # Permanent filename
            # -------------------------------------------------

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            destination_screenshot = os.path.join(
                SCREENSHOT_DIR,
                f"browser_screenshot_{timestamp}.png"
            )

            # -------------------------------------------------
            # Copy screenshot
            # -------------------------------------------------

            shutil.copy2(
                source_screenshot,
                destination_screenshot
            )

            # -------------------------------------------------
            # Verify copied screenshot
            # -------------------------------------------------

            if not os.path.isfile(
                destination_screenshot
            ):

                return (
                    "Browser screenshot was captured "
                    "but could not be saved permanently."
                )

            print(
                "\n========================================"
            )
            print(
                "Browser webpage screenshot saved:"
            )
            print(
                destination_screenshot
            )
            print(
                "========================================"
            )

            return (
                "Browser task completed successfully. "
                "Webpage screenshot saved to: "
                f"{destination_screenshot}"
            )

        # =================================================
        # NORMAL BROWSER TASK
        # =================================================

        return (
            "Browser task completed successfully."
        )

    # =====================================================
    # ERROR HANDLING
    # =====================================================

    except Exception as e:

        print(
            "\n========== BROWSER ERROR =========="
        )

        traceback.print_exc()

        print(
            "===================================\n"
        )

        return (
            f"Browser task failed: {str(e)}"
        )

    # =====================================================
    # CRITICAL CLEANUP
    # =====================================================

    finally:

        if browser_session is not None:

            print(
                "\n========================================"
            )
            print(
                "Stopping Browser Use..."
            )

            try:

                # IMPORTANT:
                # kill() actually kills the browser process.
                #
                # stop() would leave the browser alive.
                await browser_session.kill()

                print(
                    "Browser process stopped."
                )

            except Exception as cleanup_error:

                print(
                    "Browser cleanup error:"
                )

                print(
                    cleanup_error
                )

            print(
                "========================================\n"
            )


# =========================================================
# SYNCHRONOUS LANGCHAIN TOOL
# =========================================================

@tool
def browser_task(task: str) -> str:
    """
    Use this tool for tasks that require interacting with websites.

    Examples:
    - Open Google and search for Python
    - Find a GitHub profile
    - Find a product
    - Download a file
    - Fill out a web form
    - Take a webpage screenshot

    Browser Use is started only when this tool is called
    and is completely stopped when the task finishes.
    """

    return asyncio.run(
        _browser_task_async(task)
    )