import os
import json
import base64

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

import sys
sys.path.append(r"D:\coding-context-agent")

from current_context import resolve_active_location

# ============================================================
# SCREEN CONTEXT VISION LLM
# ============================================================

vision_llm = ChatOpenAI(
    base_url="https://api.deepseek.com",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    model="deepseek-flash",
    tiktoken_model_name="gpt-4o-mini",
)


# ============================================================
# DETECTOR
# ============================================================

def detect_screen_context():
    """
    Detect the currently active Windows application and,
    when relevant, the active file/folder location.

    This function is generic and does not depend on the
    user's project or workspace.
    """

    try:
        result = resolve_active_location()

        if not isinstance(result, dict):
            return {
                "status": "error",
                "reason": "Detector returned invalid data."
            }

        return result

    except Exception as e:
        return {
            "status": "error",
            "reason": str(e)
        }


# ============================================================
# SCREENSHOT
# ============================================================

def capture_screen():
    """
    Capture the current screen.

    Uses the existing screenshot tool.
    """

    try:
        from PIL import ImageGrab

        desktop = os.path.join(
            os.path.expanduser("~"),
            "Desktop"
        )

        os.makedirs(desktop, exist_ok=True)

        from datetime import datetime

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        filepath = os.path.join(
            desktop,
            f"AI_Context_{timestamp}.png"
        )

        image = ImageGrab.grab()
        image.save(filepath)

        return filepath

    except Exception as e:
        return None


# ============================================================
# VISION ANALYSIS
# ============================================================

def analyze_screen_with_vision(
    screenshot_path,
    detected_context,
):
    """
    Analyze the current screen using DeepSeek V4.1-Flash
    native vision support.

    Returns text only so the result can be injected into
    the existing main-agent pipeline.
    """

    if not screenshot_path:
        return "No screenshot was available."

    try:

        with open(
            screenshot_path,
            "rb"
        ) as f:
            image_bytes = f.read()

        image_base64 = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        context_json = json.dumps(
            detected_context,
            indent=2,
            ensure_ascii=False,
        )

        prompt = f"""
You are analyzing the user's current Windows screen.

The screen detector reported:

{context_json}

Analyze the screenshot carefully.

Determine:

1. What application is currently visible.
2. What the active window appears to contain.
3. What the user appears to be looking at.
4. Any visible file, folder, website, code, error,
   dialog, settings page, or other important content.
5. Important visible text.
6. If there is an obvious error or warning, explain it.
7. Do not invent anything that is not visible.

Give a concise but useful description.
"""

        response = vision_llm.invoke(
            [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    "data:image/png;base64,"
                                    + image_base64
                                ),
                                "detail": "low",
                            },
                        },
                    ]
                )
            ]
        )

        return response.content or (
            "The vision model did not return a description."
        )

    except Exception as e:
        return (
            f"Vision analysis failed: {e}"
        )


# ============================================================
# SCREEN REQUEST CLASSIFICATION
# ============================================================

def classify_screen_requirement(user_input):
    """
    Decide whether the current screen detector is required.

    IMPORTANT:
    This is semantic classification rather than a list of
    hardcoded user phrases.

    Returns one of:

        NONE
        DETECT
        DETECT_VISION
    """

    classifier_prompt = f"""
Classify the user's request according to whether the
CURRENT WINDOWS SCREEN CONTEXT is required.

User request:
{user_input}

Return EXACTLY one label:

NONE
DETECT
DETECT_VISION

Meaning:

NONE:
The request explicitly identifies the object/file/folder/
project/application being discussed, or the current screen
is not required.

Examples:
"find the error in fixed.py"
"analyze D:\\project\\main.py"
"open good.txt"
"send report.pdf to Ravi"

DETECT:
The request refers to something ambiguous that could mean
the currently active application, file, folder, or project.

Examples:
"identify the error in this file"
"analyze this project"
"what is wrong here"
"check this folder"
"look at this file"

DETECT_VISION:
The user explicitly asks about what is currently visible
on the screen or asks a question whose answer requires
visual screen understanding.

Examples:
"what is this"
"what is on my screen"
"what am I looking at"
"explain what is visible"
"what does this screen show"

Important:

Do not assume a particular application.

Do not assume VS Code, Kiro, Chrome, Explorer, Notepad,
Settings, or any other application.

Use only the semantic meaning of the user's request.

Return only:

NONE

or

DETECT

or

DETECT_VISION
"""

    try:

        response = vision_llm.invoke(
            [
                HumanMessage(
                    content=classifier_prompt
                )
            ]
        )

        result = (
            response.content
            .strip()
            .upper()
        )

        if "DETECT_VISION" in result:
            return "DETECT_VISION"

        if result == "DETECT" or (
            "DETECT" in result
            and "DETECT_VISION" not in result
        ):
            return "DETECT"

        return "NONE"

    except Exception:
        return "NONE"


# ============================================================
# MAIN SCREEN-CONTEXT LAYER
# ============================================================

def prepare_screen_context(user_input):
    """
    Top-level screen-context layer.

    This does NOT execute the main agent.

    It only decides whether screen context should be added
    before the existing agent pipeline runs.
    """

    requirement = classify_screen_requirement(
        user_input
    )

    print(
        f"[Screen context] Mode: {requirement}"
    )

    # --------------------------------------------------------
    # Normal request
    # --------------------------------------------------------

    if requirement == "NONE":

        return user_input

    # --------------------------------------------------------
    # Detect active application/file/folder
    # --------------------------------------------------------

    detected = detect_screen_context()

    print(
        "[Screen context] Detector result:"
    )

    print(
        json.dumps(
            detected,
            indent=2,
            ensure_ascii=False,
        )
    )

    # --------------------------------------------------------
    # Vision request
    # --------------------------------------------------------

    if requirement == "DETECT_VISION":

        screenshot = capture_screen()

        print(
            "[Screen context] Screenshot:"
            f" {screenshot}"
        )

        vision_result = analyze_screen_with_vision(
            screenshot,
            detected,
        )

        return f"""
USER REQUEST:
{user_input}

CURRENT SCREEN CONTEXT:
{json.dumps(detected, indent=2, ensure_ascii=False)}

CURRENT SCREEN VISUAL ANALYSIS:
{vision_result}

Use this screen context to answer the user's request.
Do not mention internal screen-context implementation.
Do not claim anything that is not supported by the
detected context or visual analysis.

USER REQUEST TO COMPLETE:
{user_input}
""".strip()

    # --------------------------------------------------------
    # Detector-only request
    # --------------------------------------------------------

    return f"""
USER REQUEST:
{user_input}

CURRENT ACTIVE WINDOWS CONTEXT:
{json.dumps(detected, indent=2, ensure_ascii=False)}

Use the detected application/file/folder context to
understand what the user means by "this", "here", "this
file", "this folder", "this project", etc.

If a full file/folder path was detected, use that exact path.

If no path was detected, do not invent one.

USER REQUEST TO COMPLETE:
{user_input}
""".strip()