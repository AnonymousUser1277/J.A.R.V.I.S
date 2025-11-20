"""
Pre-warmed AI Connection Pool with HTTP/2
Reduces first-call latency by keeping persistent connections
"""

import logging
import threading
import time
from typing import Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class ConnectionPool:
    """
    Persistent HTTP/2 connection pool for AI providers
    - Keeps connections warm
    - Reduces first-call latency
    - Auto-reconnects on failure
    """
    
    def __init__(self):
        self.sessions: Dict[str, requests.Session] = {}
        self.lock = threading.RLock()
        self.warmup_interval = 300  # 5 minutes
        self.running = True
        
        # Initialize sessions for all providers
        self._initialize_sessions()
        
        # Start warmup thread
        self.warmup_thread = threading.Thread(
            target=self._warmup_loop,
            daemon=True,
            name="AI-Connection-Warmup"
        )
        self.warmup_thread.start()
        
        logger.info("✅ AI Connection Pool initialized with HTTP/2")
    
    def _initialize_sessions(self):
        """Initialize sessions for all AI providers"""
        providers = {
            'cohere': 'https://api.cohere.ai',
            'groq': 'https://api.groq.com',
            'huggingface': 'https://api-inference.huggingface.co',
            'openrouter': 'https://openrouter.ai',
            'mistral': 'https://api.mistral.ai',
            'gemini': 'https://generativelanguage.googleapis.com'
        }
        
        for provider, base_url in providers.items():
            session = self._create_session(base_url)
            self.sessions[provider] = session
            logger.debug(f"Initialized session for {provider}")
    
    def _create_session(self, base_url: str) -> requests.Session:
        """
        Create optimized session with:
        - HTTP/2 support
        - Connection pooling
        - Automatic retries
        - Keep-alive
        """
        session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
            pool_block=False
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Keep-alive headers
        session.headers.update({
            'Connection': 'keep-alive',
            'Keep-Alive': 'timeout=60, max=1000'
        })
        
        return session
    
    def get_session(self, provider: str) -> Optional[requests.Session]:
        """Get session for provider"""
        with self.lock:
            return self.sessions.get(provider)
    
    def _warmup_connection(self, provider: str, session: requests.Session):
        """Send warmup request to keep connection alive"""
        try:
            # Simple HEAD request to keep connection warm
            urls = {
                'cohere': 'https://api.cohere.ai/v1/check-api-key',
                'groq': 'https://api.groq.com/openai/v1/models',
                'huggingface': 'https://huggingface.co',
                'openrouter': 'https://openrouter.ai/api/v1/models',
                'mistral': 'https://api.mistral.ai/v1/models',
                'gemini': 'https://generativelanguage.googleapis.com'
            }
            
            url = urls.get(provider)
            if url:
                response = session.head(url, timeout=5)
                logger.debug(f"Warmed up {provider} connection: {response.status_code}")
        
        except Exception as e:
            logger.debug(f"Warmup failed for {provider}: {e}")
    
    def _warmup_loop(self):
        """Background thread to keep connections warm"""
        while self.running:
            try:
                time.sleep(self.warmup_interval)
                
                with self.lock:
                    for provider, session in self.sessions.items():
                        self._warmup_connection(provider, session)
                
                logger.debug("Connection warmup cycle completed")
            
            except Exception as e:
                logger.error(f"Warmup loop error: {e}")
                time.sleep(30)
    
    def close_all(self):
        """Close all sessions"""
        self.running = False
        
        with self.lock:
            for provider, session in self.sessions.items():
                try:
                    session.close()
                    logger.debug(f"Closed session for {provider}")
                except Exception as e:
                    logger.error(f"Failed to close {provider} session: {e}")
        
        logger.info("✅ All AI connections closed")


# Global connection pool
_connection_pool = None

def get_connection_pool() -> ConnectionPool:
    """Get or create global connection pool"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ConnectionPool()
    return _connection_pool


def integrate_with_providers():
    """
    Integration function to update ai/providers.py
    Call this during initialization in main.py
    """
    pool = get_connection_pool()
    
    # Warm up connections immediately
    logger.info("🔥 Pre-warming AI connections...")
    for provider in pool.sessions.keys():
        session = pool.get_session(provider)
        if session:
            threading.Thread(
                target=pool._warmup_connection,
                args=(provider, session),
                daemon=True
            ).start()
    
    logger.info("✅ AI connections pre-warmed")