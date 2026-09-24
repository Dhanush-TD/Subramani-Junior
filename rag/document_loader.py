import os
from pathlib import Path

from pypdf import PdfReader
from docx import Document


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".json",
    ".csv",
    ".log",
    ".pdf",
    ".docx",
}


def read_text_file(file_path: str) -> str:
    """
    Read normal text-based files.
    """

    try:
        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:
            return file.read()

    except Exception:
        return ""


def read_pdf(file_path: str) -> str:
    """
    Extract text from a PDF.
    """

    try:

        reader = PdfReader(file_path)

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        return "\n".join(pages)

    except Exception:
        return ""


def read_docx(file_path: str) -> str:
    """
    Extract text from a Word document.
    """

    try:

        document = Document(file_path)

        paragraphs = []

        for paragraph in document.paragraphs:

            if paragraph.text.strip():
                paragraphs.append(
                    paragraph.text
                )

        return "\n".join(paragraphs)

    except Exception:
        return ""


def load_document(file_path: str) -> str:
    """
    Load content from a supported file.
    """

    if not file_path:
        return ""

    path = Path(file_path)

    if not path.is_file():
        return ""

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return ""

    if extension == ".pdf":
        return read_pdf(file_path)

    if extension == ".docx":
        return read_docx(file_path)

    return read_text_file(file_path)