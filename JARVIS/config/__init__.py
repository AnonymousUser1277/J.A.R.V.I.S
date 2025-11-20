"""
Configuration package
"""

from .settings import *
from .api_keys import *
from .sentences_list import *
from .loader import *
__all__ = [
    'PROJECT_ROOT', 'DATA_DIR', 'CACHE_DIR', 'HISTORY_DIR', 'LOG_DIR',
    'MAX_HISTORY', 'HISTORY_FILE', 'STOP_WORDS', 'IGNORE_WORDS',
    'EXCLUDE_KEYWORDS', 'DESTRUCTIVE_KEYWORDS',
    'setup_environment', 'get_os_info',
    'COHERE_KEYS', 'GROQ_KEYS', 'GEMINI_KEYS', 'HUGGINGFACE_KEYS',
    'OPENROUTER_KEYS', 'MISTRAL_KEYS','ASSISTANT_VOICE',
    'RELEVANCE_KEYS', 'HYPERBOLIC_KEYS', 'AIMLAPI_KEYS',
    'new_task_responses','repeat_task_responses',
    'accepted_lines','rejected_pending_lines',
    'open_editor_lines','cache_removed_lines','settings'
]