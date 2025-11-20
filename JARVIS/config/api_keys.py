"""
API key management with automatic failover
"""

import os
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()
def get_api_keys(prefix: str, count: int = 3) -> List[Dict[str, str]]:
    """Get API keys from environment with naming convention"""
    keys = []
    
    for i in range(1, count + 1):
        key_name = f"{prefix}_KEY_{i}"
        key_value = os.getenv(key_name)
        
        if key_value:
            keys.append({
                "name": f"{prefix} Key {i}",
                "key": key_value
            })
    
    return keys

# API Keys
COHERE_KEYS = get_api_keys("COHERE")
GROQ_KEYS = get_api_keys("GROQ")
HUGGINGFACE_KEYS = get_api_keys("HUGGINGFACE")
OPENROUTER_KEYS = get_api_keys("OPENROUTER")
MISTRAL_KEYS = get_api_keys("MISTRAL")

GEMINI_KEYS = [
    os.getenv("GEMINI_KEY_1"),
    os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3")
]
# Filter out None values
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]