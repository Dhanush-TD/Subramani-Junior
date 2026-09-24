from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from .config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


# =========================================================
# TEXT SPLITTER
# =========================================================

text_splitter = RecursiveCharacterTextSplitter(

    chunk_size=CHUNK_SIZE,

    chunk_overlap=CHUNK_OVERLAP,

    separators=[
        "\n\n",
        "\n",
        " ",
        "",
    ],

)


# =========================================================
# CHUNK TEXT
# =========================================================

def chunk_text(
    text: str,
    file_path: str
):

    """
    Convert file text into smaller documents.

    Every chunk keeps the original file path
    inside metadata.
    """

    if not text:

        return []


    documents = (
        text_splitter.create_documents(

            [text],

            metadatas=[

                {
                    "source": file_path
                }

            ]

        )
    )


    return documents