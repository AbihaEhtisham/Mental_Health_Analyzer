import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
import os

# Pakistan Standard Time (UTC+5)
PKT = timezone(timedelta(hours=5))


def get_pkt_now():
    """Get current time in Pakistan Standard Time."""
    return datetime.now(PKT).strftime("%Y-%m-%d %H:%M:%S")

DB_PATH = os.path.join(os.path.dirname(__file__), "mood_tracker.db")


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create mood_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            answers TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Create chat_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood_log_id INTEGER NOT NULL,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (mood_log_id) REFERENCES mood_logs (id)
        )
    """)

    # Create chat_messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
        )
    """)

    conn.commit()
    conn.close()


def create_user(username: str) -> Optional[int]:
    """Create a new user. Returns user_id or None if username exists."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, created_at) VALUES (?, ?)",
            (username, get_pkt_now())
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_user(username: str) -> Optional[Dict]:
    """Get user by username."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"id": row["id"], "username": row["username"], "created_at": row["created_at"]}
    return None


def user_exists(username: str) -> bool:
    """Check if username exists."""
    return get_user(username) is not None


def save_mood_log(user_id: int, mood: str, answers: str) -> int:
    """Save a mood log entry. Returns the log id."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO mood_logs (user_id, mood, answers, created_at) VALUES (?, ?, ?, ?)",
        (user_id, mood, answers, get_pkt_now())
    )
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id


def get_user_mood_history(username: str) -> List[Dict]:
    """Get all mood logs for a user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ml.id, ml.mood, ml.answers, ml.created_at
        FROM mood_logs ml
        JOIN users u ON ml.user_id = u.id
        WHERE u.username = ?
        ORDER BY ml.created_at DESC
    """, (username,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "mood": row["mood"],
            "answers": row["answers"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]


# ============== CHAT SESSION FUNCTIONS ==============

def create_chat_session(user_id: int, mood_log_id: int) -> int:
    """Create a new chat session. Returns session id."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chat_sessions (user_id, mood_log_id, started_at) VALUES (?, ?, ?)",
        (user_id, mood_log_id, get_pkt_now())
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def end_chat_session(session_id: int):
    """Mark a chat session as ended."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE chat_sessions SET ended_at = ? WHERE id = ?",
        (get_pkt_now(), session_id)
    )
    conn.commit()
    conn.close()


def save_chat_message(session_id: int, role: str, content: str) -> int:
    """Save a chat message. Returns message id."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, role, content, get_pkt_now())
    )
    conn.commit()
    message_id = cursor.lastrowid
    conn.close()
    return message_id


def get_session_messages(session_id: int) -> List[Dict]:
    """Get all messages for a chat session."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role, content, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY created_at ASC
    """, (session_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]


def get_user_chat_sessions(username: str) -> List[Dict]:
    """Get all chat sessions for a user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT cs.id, cs.mood_log_id, cs.started_at, cs.ended_at, ml.mood
        FROM chat_sessions cs
        JOIN users u ON cs.user_id = u.id
        JOIN mood_logs ml ON cs.mood_log_id = ml.id
        WHERE u.username = ?
        ORDER BY cs.started_at DESC
    """, (username,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "mood_log_id": row["mood_log_id"],
            "mood": row["mood"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"]
        }
        for row in rows
    ]


def get_latest_mood_log(username: str) -> Optional[Dict]:
    """Get the most recent mood log for a user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ml.id, ml.mood, ml.answers, ml.created_at
        FROM mood_logs ml
        JOIN users u ON ml.user_id = u.id
        WHERE u.username = ?
        ORDER BY ml.created_at DESC
        LIMIT 1
    """, (username,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row["id"],
            "mood": row["mood"],
            "answers": row["answers"],
            "created_at": row["created_at"]
        }
    return None


# Initialize database on import
init_db()
