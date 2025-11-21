"""
Redis-based cache system with stable HASH-key architecture
Fixed: Removed 'enabled' flag trap, added protection signal
"""

import redis
import hashlib
import threading
import logging
import time
import json

logger = logging.getLogger(__name__)

class FastCache:
    """Thread-safe Redis cache engine"""

    def __init__(self):
        # We try to connect, but we won't permanently disable if it fails once.
        # We will try/except every operation.
        try:
            self.db = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True
            )
            self.db.ping()
            logger.info("✅ Redis Cache Connected")
        except Exception as e:
            logger.error(f"⚠️ Redis unavailable at startup: {e}")
            self.db = None # Mark as None to indicate failure

        self.lock = threading.RLock()

    # -------------------------------------------------
    # HASH key generator (Normalized)
    # -------------------------------------------------
    def _hash_key(self, prompt):
        # Normalize: Lowercase, strip space, remove common punctuation
        normalized = prompt.lower().strip().rstrip(".?!")
        return hashlib.sha256(normalized.encode()).hexdigest()

    # -------------------------------------------------
    # MAIN GET
    # -------------------------------------------------
    def get(self, prompt):
        if not self.db: return None
        
        try:
            key = self._hash_key(prompt)
            d = self.db.hgetall(key)

            if d and d.get("status") == "accepted":
                # Update stats in background
                threading.Thread(
                    target=self._update_access,
                    args=(key,),
                    daemon=True
                ).start()
                return d.get("response")
        except Exception as e:
            logger.error(f"Cache GET error: {e}")
            
        return None

    # -------------------------------------------------
    # SET pending (Protected)
    # -------------------------------------------------
    def set_pending(self, prompt, response):
        if not self.db: return None
        
        try:
            key = self._hash_key(prompt)
            
            # PROTECTION: Check if this key already exists and is accepted
            if self.db.exists(key):
                status = self.db.hget(key, "status")
                if status == "accepted":
                    logger.info(f"🛡️ Cache protection: Key '{key[:8]}' is already accepted. Skipping pending set.")
                    return None # Signal that we did NOT create a new pending entry

            now = time.time()

            def force_str(val):
                if val is None: return ""
                if isinstance(val, (dict, list)): return json.dumps(val, ensure_ascii=False)
                return str(val)

            mapping = {
                "prompt": force_str(prompt),
                "response": force_str(response),
                "status": "pending",
                "created_at": str(now),
                "last_accessed": str(now),
                "access_count": "1"
            }

            self.db.hmset(key, mapping)
            return key
            
        except Exception as e:
            logger.error(f"Cache SET error: {e}")
            return None

    # -------------------------------------------------
    # ACCEPT / REJECT
    # -------------------------------------------------
    def accept(self, key):
        if self.db: self.db.hset(key, "status", "accepted")

    def reject(self, key):
        if self.db: self.db.hset(key, "status", "rejected")

    def delete(self, key):
        if self.db: self.db.delete(key)

    # -------------------------------------------------
    # EXPORT / IMPORT / STATS (For Editor)
    # -------------------------------------------------
    def get_stats(self):
        if not self.db: return {}
        stats = {"total_entries": 0, "accepted": 0, "pending": 0, "rejected": 0, "total_hits": 0}
        try:
            for key in self.db.scan_iter():
                d = self.db.hgetall(key)
                if d:
                    stats["total_entries"] += 1
                    stats[d.get("status", "unknown")] = stats.get(d.get("status", "unknown"), 0) + 1
                    stats["total_hits"] += int(d.get("access_count") or 0)
        except: pass
        return stats

    def export_to_dict(self, include_rejected=True):
        if not self.db: return {}
        out = {}
        try:
            for key in self.db.scan_iter():
                d = self.db.hgetall(key)
                if d:
                    if not include_rejected and d.get("status") == "rejected": continue
                    out[key] = d
        except: pass
        return out

    def import_from_dict(self, data, clear_existing=False):
        if not self.db: return
        if clear_existing: self.db.flushdb()
        for key, fields in data.items():
            self.db.hmset(key, fields)

    def _update_access(self, key):
        try:
            if self.db and self.db.exists(key):
                self.db.hincrby(key, "access_count", 1)
                self.db.hset(key, "last_accessed", time.time())
        except: pass

# Global
cache = FastCache()
