"""Semantic Cache for frequent queries."""

import sqlite3
import json
import time
import numpy as np

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

SIMILARITY_THRESHOLD = 0.85

class SemanticCache:
    """Semantic similarity based cache with TTL."""
    
    def __init__(self, db_path: str = "data/voxagent.db"):
        self.db_path = db_path
        self.embedder = None
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
                query TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                embedding BLOB NOT NULL,
                result TEXT NOT NULL,
                created_at REAL NOT NULL,
                ttl INTEGER NOT NULL,
                hit_count INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
    
    def _get_embedder(self):
        if self.embedder is None:
            try:
                # Try to reuse KB's embedder to save memory
                from app.rag.knowledge_base import kb
                if kb.embedder is not None:
                    self.embedder = kb.embedder
                    print("⚡ Cache reusing KB embedder (saved ~80MB RAM)")
                else:
                    from sentence_transformers import SentenceTransformer
                    self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                print(f"⚠️ Cache embedder load failed: {e}")
        return self.embedder
    
    def _get_embedding(self, text: str) -> np.ndarray:
        embedder = self._get_embedder()
        if embedder is None:
            return None
        return embedder.encode([text])[0]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 0
        return float(dot / norm)
    
    def get(self, query: str, tool_name: str) -> dict | None:
        """Get cached result if similar query exists and TTL is valid."""
        ttl = CACHE_TTL.get(tool_name, 0)
        if ttl == 0:
            return None
        
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
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
            
            cached_embedding = np.frombuffer(row["embedding"], dtype=np.float32)
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
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
        
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return
        
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO semantic_cache (query, tool_name, embedding, result, created_at, ttl) VALUES (?, ?, ?, ?, ?, ?)",
            (query, tool_name, query_embedding.tobytes(), json.dumps(result, ensure_ascii=False), time.time(), ttl)
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
