"""Lightweight Semantic Cache — no ML model needed."""

import sqlite3
import json
import time
import re

CACHE_TTL = {
    "get_weather":        1800,
    "search_web":         3600,
    "search_knowledge":   86400,
    "lookup_customer":    0,
    "book_appointment":   0,
    "get_bookings":       0,
    "update_booking":     0,
    "cancel_booking":     0,
    "get_current_time":   0,
}

SIMILARITY_THRESHOLD = 0.65

class SemanticCache:
    """Word-overlap based cache with TTL. No ML model needed."""
    
    def __init__(self, db_path: str = "data/voxagent.db"):
        self.db_path = db_path
        self._init_db()
        print("⚡ Semantic cache ready!")
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS semantic_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                tool_name TEXT,
                embedding BLOB,
                result TEXT,
                created_at REAL,
                ttl INTEGER,
                hit_count INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
    
    def _tokenize(self, text: str) -> set:
        """Extract meaningful words from text."""
        text = text.lower().strip()
        words = set(re.findall(r'\b\w{2,}\b', text))
        # Remove stop words
        stop = {'the','is','in','at','to','of','and','or','for','on','by','it','me','my','do','no','so','if','he','we','an','as','am','ka','ke','ki','hai','kya','ko','se','ne','ye','wo','toh','bhi','karo','kar','tell','what','who','how','when','where','which','was','were','are','been','can','will','did','does','has','had','have','this','that','with','from'}
        return words - stop
    
    def _similarity(self, q1: str, q2: str) -> float:
        """Word overlap similarity (Jaccard)."""
        s1 = self._tokenize(q1)
        s2 = self._tokenize(q2)
        if not s1 or not s2:
            return 0.0
        intersection = len(s1 & s2)
        union = len(s1 | s2)
        return intersection / union if union > 0 else 0.0
    
    def get(self, query: str, tool_name: str) -> dict | None:
        """Get cached result if similar query exists and TTL is valid."""
        ttl = CACHE_TTL.get(tool_name, 0)
        if ttl == 0:
            return None
        
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM semantic_cache WHERE tool_name = ?",
            (tool_name,)
        ).fetchall()
        
        best_match = None
        best_similarity = 0
        
        for row in rows:
            age = time.time() - row["created_at"]
            if age > row["ttl"]:
                conn.execute("DELETE FROM semantic_cache WHERE id = ?", (row["id"],))
                continue
            
            similarity = self._similarity(query, row["query"])
            
            if similarity > best_similarity and similarity >= SIMILARITY_THRESHOLD:
                best_similarity = similarity
                best_match = row
        
        conn.commit()
        
        if best_match:
            conn.execute(
                "UPDATE semantic_cache SET hit_count = hit_count + 1 WHERE id = ?",
                (best_match["id"],)
            )
            conn.commit()
            conn.close()
            
            result = json.loads(best_match["result"])
            print(f"⚡ Cache HIT! tool={tool_name} sim={best_similarity:.2f} hits={best_match['hit_count']+1}")
            return result
        
        conn.close()
        print(f"💨 Cache MISS: tool={tool_name} query='{query[:50]}'")
        return None
    
    def set(self, query: str, tool_name: str, result: dict):
        """Save result to cache with TTL."""
        ttl = CACHE_TTL.get(tool_name, 0)
        if ttl == 0:
            return
        
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO semantic_cache (query, tool_name, embedding, result, created_at, ttl) VALUES (?, ?, ?, ?, ?, ?)",
            (query, tool_name, b"", json.dumps(result, ensure_ascii=False), time.time(), ttl)
        )
        conn.commit()
        conn.close()
        
        print(f"💾 Cached: tool={tool_name} query='{query[:50]}' TTL={ttl}s")
    
    def get_stats(self) -> dict:
        """Get cache stats."""
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM semantic_cache").fetchone()[0]
        total_hits = conn.execute("SELECT SUM(hit_count) FROM semantic_cache").fetchone()[0] or 0
        conn.close()
        return {"cached_queries": total, "total_hits": total_hits}

cache = SemanticCache()
