"""
Redis-based cache system with stable HASH-key architecture
Compatible with your Cache Editor + Backup Manager
"""

import redis
import hashlib
import threading
import logging
import time
import json
logger = logging.getLogger(__name__)
import os
# print("🔍 REDIS CACHE LOADED FROM:", os.path.abspath(__file__))

class FastCache:
    """Thread-safe Redis cache engine"""

    def __init__(self):
        self.enabled = False
        try:
            self.db = redis.Redis(
                host="localhost",
                port=6379,
                db=0,
                decode_responses=True       # easier & cleaner
            )
            self.db.ping()
        except Exception as e:
            logger.error(f"⚠️ Redis unavailable. Caching disabled. Error: {e}")
            self.enabled = False

        self.lock = threading.RLock()

    # -------------------------------------------------
    # HASH key generator (always SHA-256)
    # -------------------------------------------------
    def _hash_key(self, prompt):
        return hashlib.sha256(prompt.encode()).hexdigest()

    # -------------------------------------------------
    # MAIN GET
    # -------------------------------------------------
    def get(self, prompt):
        if not self.enabled:
            return None
        key = self._hash_key(prompt)
        d = self.db.hgetall(key)

        if d and d.get("status") == "accepted":
            threading.Thread(
                target=self._update_access,
                args=(key,),
                daemon=True
            ).start()
            return d.get("response")

        return None

    # -------------------------------------------------
    # SET pending
    # -------------------------------------------------
    



    def set_pending(self, prompt, response):
        key = self._hash_key(prompt)
        now = time.time()

        # universal sanitizer — nothing gets into Redis unless it's a string or JSON
        def force_str(val):
            if val is None:
                return ""
            if isinstance(val, (dict, list)):
                return json.dumps(val, ensure_ascii=False)
            try:
                return str(val)
            except:
                return json.dumps({"invalid": True, "value": repr(val)})

        prompt_str = force_str(prompt)
        response_str = force_str(response)

        mapping = {
            "prompt": prompt_str,
            "response": response_str,
            "status": "pending",
            "created_at": str(now),
            "last_accessed": str(now),
            "access_count": "1"
        }

        # ensure every value is final string
        mapping = {k: force_str(v) for k, v in mapping.items()}
        # print("DEBUG PROMPT:", type(prompt_str), prompt_str[:100])
        # print("DEBUG RESPONSE:", type(response_str), response_str[:100])

        # print("FINAL MAPPING:", mapping)
        # for k, v in mapping.items():
        #     print("FIELD:", repr(k), "VALUE:", repr(v))

        self.db.hmset(key, mapping)
        # FIX: Return the key itself, not the result of the hmset command
        return key





    # -------------------------------------------------
    # ACCEPT / REJECT
    # -------------------------------------------------
    def accept(self, key):
        self.db.hset(key, "status", "accepted")

    def reject(self, key):
        self.db.hset(key, "status", "rejected")

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------
    def delete(self, key):
        self.db.delete(key)

    # -------------------------------------------------
    # GET by key
    # -------------------------------------------------
    def get_by_key(self, key):
        return self.db.hgetall(key) or None

    # -------------------------------------------------
    # UPDATE access stats
    # -------------------------------------------------
    def _update_access(self, key):
        with self.lock:
            if self.db.exists(key):
                self.db.hincrby(key, "access_count", 1)
                self.db.hset(key, "last_accessed", time.time())

    # -------------------------------------------------
    # CLEANUP
    # -------------------------------------------------
    def cleanup_old_entries(self, days=30):
        cutoff = time.time() - days * 86400

        for key in self.db.scan_iter():
            try:
                last = float(self.db.hget(key, "last_accessed") or 0)
                if last < cutoff:
                    self.db.delete(key)
            except:
                pass

    # -------------------------------------------------
    # STATS
    # -------------------------------------------------
    def get_stats(self):
        stats = {
            "total_entries": 0,
            "accepted": 0,
            "pending": 0,
            "rejected": 0,
            "total_hits": 0,
            "avg_hits_per_entry": 0
        }

        for key in self.db.scan_iter():
            d = self.db.hgetall(key)
            if not d:
                continue

            stats["total_entries"] += 1
            status = d.get("status")

            if status == "accepted":
                stats["accepted"] += 1
            elif status == "pending":
                stats["pending"] += 1
            elif status == "rejected":
                stats["rejected"] += 1

            stats["total_hits"] += int(d.get("access_count") or 0)

        if stats["total_entries"]:
            stats["avg_hits_per_entry"] = stats["total_hits"] / stats["total_entries"]

        return stats

    # -------------------------------------------------
    # EXPORT FULL CACHE (hash_key → full_data)
    # -------------------------------------------------
    def export_to_dict(self, include_rejected=True):
        out = {}

        for key in self.db.scan_iter():
            d = self.db.hgetall(key)
            if not d:
                continue

            if not include_rejected and d.get("status") == "rejected":
                continue

            # SAFEST: store using Redis hash key
            out[key] = d

        return out

    # -------------------------------------------------
    # IMPORT FULL CACHE
    # -------------------------------------------------
    def import_from_dict(self, data, clear_existing=False):
        if clear_existing:
            self.db.flushdb()

        for key, fields in data.items():
            self.db.hmset(key, fields)

    # -------------------------------------------------
    # GET pending entries
    # -------------------------------------------------
    def get_pending_entries(self):
        out = []
        for key in self.db.scan_iter():
            d = self.db.hgetall(key)
            if d.get("status") == "pending":
                out.append({
                    "key": key,
                    "prompt": d.get("prompt"),
                    "response": d.get("response")
                })
        return out


# Global
cache = FastCache()
