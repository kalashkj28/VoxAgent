"""Persistent memory using SQLite."""

import sqlite3
import os
import uuid
from datetime import datetime

class MemoryStore:
    """SQLite-based persistent memory store."""
    
    def __init__(self, db_path: str = "data/voxagent.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
        print(f"💾 Memory store ready: {os.path.abspath(db_path)}")
    
    def _get_conn(self):
        """Get thread-safe DB connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ended_at DATETIME,
                message_count INTEGER DEFAULT 0,
                summary TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                preferences TEXT,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_sessions INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())[:8]
        
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO sessions (id) VALUES (?)",
            (session_id,)
        )
        conn.commit()
        conn.close()
        
        print(f"📋 New session: {session_id}")
        return session_id
    
    def end_session(self, session_id: str, summary: str = ""):
        """End a session with an optional summary."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE sessions SET ended_at = ?, summary = ? WHERE id = ?",
            (datetime.now().isoformat(), summary, session_id)
        )
        conn.commit()
        conn.close()
    
    def save_message(self, session_id: str, role: str, content: str):
        """Save a single message."""
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        conn.execute(
            "UPDATE sessions SET message_count = message_count + 1 WHERE id = ?",
            (session_id,)
        )
        conn.commit()
        conn.close()
    
    def get_session_messages(self, session_id: str, limit: int = 20) -> list:
        """Get recent messages from a session in Gemini format."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
        conn.close()
        
        messages = [{"role": row["role"], "parts": [row["content"]]} for row in reversed(rows)]
        return messages
    
    def get_past_context(self, limit: int = 5) -> str:
        """Get summarized context from past sessions."""
        conn = self._get_conn()
        
        sessions = conn.execute(
            "SELECT id, started_at, message_count, summary FROM sessions ORDER BY started_at DESC LIMIT ?",
            (limit + 1,)
        ).fetchall()
        
        if len(sessions) <= 1:
            conn.close()
            return ""
        
        context_parts = []
        
        for session in sessions[1:]:
            sid = session["id"]
            
            if session["summary"]:
                context_parts.append(f"Past session ({session['started_at']}): {session['summary']}")
            else:
                msgs = conn.execute(
                    "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT 6",
                    (sid,)
                ).fetchall()
                
                if msgs:
                    snippets = []
                    for m in reversed(msgs):
                        prefix = "User" if m["role"] == "user" else "Agent"
                        snippets.append(f"{prefix}: {m['content'][:100]}")
                    context_parts.append(
                        f"Past session ({session['started_at']}):\n" + "\n".join(snippets)
                    )
        
        conn.close()
        
        if not context_parts:
            return ""
        
        return "=== PAST CONVERSATIONS ===\n" + "\n\n".join(context_parts) + "\n=========================="
    
    def update_user(self, name: str = None, preferences: str = None):
        """Update user profile."""
        conn = self._get_conn()
        
        user = conn.execute("SELECT * FROM users LIMIT 1").fetchone()
        
        if user:
            if name:
                conn.execute("UPDATE users SET name = ?, last_seen = ? WHERE id = ?",
                           (name, datetime.now().isoformat(), user["id"]))
            if preferences:
                existing = user["preferences"] or ""
                if preferences not in existing:
                    updated = (existing + ", " + preferences).strip(", ")
                    conn.execute("UPDATE users SET preferences = ?, last_seen = ? WHERE id = ?",
                               (updated, datetime.now().isoformat(), user["id"]))
        else:
            conn.execute(
                "INSERT INTO users (name, preferences, total_sessions) VALUES (?, ?, 1)",
                (name or "Unknown", preferences or "")
            )
        
        conn.commit()
        conn.close()
    
    def track_interaction(self, user_text: str, tool_name: str = None):
        """Auto-build user profile from interactions."""
        conn = self._get_conn()
        user = conn.execute("SELECT * FROM users LIMIT 1").fetchone()
        
        if not user:
            conn.execute("INSERT INTO users (name, preferences, total_sessions) VALUES (?, ?, 1)",
                        ("Unknown", ""))
            conn.commit()
            user = conn.execute("SELECT * FROM users LIMIT 1").fetchone()
        
        prefs = user["preferences"] or ""
        updated = False
        
        hindi_words = ["kya", "hai", "bhai", "bata", "kar", "mera", "kab", "kaise"]
        has_hindi = any(w in user_text.lower().split() for w in hindi_words)
        
        if has_hindi and "lang:hinglish" not in prefs:
            prefs = (prefs + ", lang:hinglish").strip(", ")
            updated = True
        elif not has_hindi and "lang:english" not in prefs and "lang:hinglish" not in prefs:
            prefs = (prefs + ", lang:english").strip(", ")
            updated = True
        
        if tool_name:
            topic_map = {
                "get_weather": "topic:weather",
                "search_web": "topic:news",
                "search_knowledge": "topic:documents",
                "book_appointment": "topic:scheduling",
                "lookup_customer": "topic:crm",
            }
            topic = topic_map.get(tool_name, "")
            if topic and topic not in prefs:
                prefs = (prefs + ", " + topic).strip(", ")
                updated = True
        
        if updated:
            conn.execute("UPDATE users SET preferences = ?, last_seen = ? WHERE id = ?",
                        (prefs, datetime.now().isoformat(), user["id"]))
            conn.commit()
        
        conn.close()
    
    def get_user(self) -> dict:
        """Get user profile."""
        conn = self._get_conn()
        user = conn.execute("SELECT * FROM users LIMIT 1").fetchone()
        conn.close()
        
        if user:
            return {
                "name": user["name"],
                "preferences": user["preferences"],
                "first_seen": user["first_seen"],
                "last_seen": user["last_seen"],
                "total_sessions": user["total_sessions"]
            }
        return None
    
    def get_stats(self) -> dict:
        """Get memory statistics."""
        conn = self._get_conn()
        
        total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        
        conn.close()
        
        return {
            "total_messages": total_messages,
            "total_sessions": total_sessions,
            "db_path": os.path.abspath(self.db_path)
        }

memory = MemoryStore()
