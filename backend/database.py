import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).resolve().parent.parent / "store" / "messages.db"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id)
                REFERENCES conversations(id)
                ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def create_conversation(title="New Chat"):
    now = datetime.now().isoformat()

    conn = get_connection()

    cursor = conn.execute(
        """
        INSERT INTO conversations
        (title, created_at, updated_at)
        VALUES (?, ?, ?)
        """,
        (title, now, now),
    )

    conversation_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return conversation_id


def get_conversations():
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, title, created_at, updated_at
        FROM conversations
        ORDER BY updated_at DESC
        """
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_messages(conversation_id):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, conversation_id, role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
        """,
        (conversation_id,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def add_message(conversation_id, role, content):
    now = datetime.now().isoformat()

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO messages
        (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (conversation_id, role, content, now),
    )

    conn.execute(
        """
        UPDATE conversations
        SET updated_at = ?
        WHERE id = ?
        """,
        (now, conversation_id),
    )

    conn.commit()
    conn.close()


def update_conversation_title(conversation_id, title):
    conn = get_connection()

    conn.execute(
        """
        UPDATE conversations
        SET title = ?
        WHERE id = ?
        """,
        (title, conversation_id),
    )

    conn.commit()
    conn.close()


init_database()