"""
AI provider management with automatic failover
Cohere → Groq → HuggingFace → OpenRouter → Mistral → Anakin → Relevance → Hyperbolic → AIMLAPI
"""
import time
import logging
from config.api_keys import (
    COHERE_KEYS, GROQ_KEYS, HUGGINGFACE_KEYS,
    OPENROUTER_KEYS, MISTRAL_KEYS
)

logger = logging.getLogger(__name__)

# Track current provider
current_provider = "groq"
current_key_indices = {
    'cohere': 0,
    'groq': 0,
    'huggingface': 0,
    'openrouter': 0,
    'mistral': 0
}

# Client instances
groq_client = None

def setup_ai_providers(startup_ui=None):
    if startup_ui:
        startup_ui.update_status("Setting up AI...")
    
    client = setup_cohere_model()
    
    if client is None:
        logger.warning("⚠️ Cohere initialization failed. Trying Groq...")
        # ✅ Try Groq immediately, not in background
        global groq_client
        groq_client = setup_groq_model()
        if groq_client:
            logger.info("✅ Using Groq as primary provider")
            global current_provider
            current_provider = "groq"
            return groq_client
        else:
            logger.error("❌ All providers failed!")
            return None
    
    # Pre-initialize backup providers in background
    import threading
    def init_backups():
        global groq_client
        if startup_ui:
            startup_ui.update_status("Pre-loading backup AI providers...")
        if groq_client is None:
            groq_client = setup_groq_model()
        setup_huggingface_client()
        setup_openrouter_client()
        setup_mistral_client()
    threading.Thread(target=init_backups, daemon=True).start()
    return client


# ============= COHERE =============

def setup_cohere_model():
    """Initialize Cohere with first available key"""
    import cohere
    
    for i, entry in enumerate(COHERE_KEYS):
        try:
            co = cohere.Client(api_key=entry["key"])
            logger.info(f"✅ Using Cohere {entry['name']} key")
            current_key_indices['cohere'] = i
            return co
        except Exception as e:
            logger.error(f"❌ Cohere {entry['name']} key failed: {e}")
    
    logger.error("❌ All Cohere API keys failed!")
    return None

def switch_to_next_cohere_key(client):
    """Switch to next available Cohere API key"""
    import cohere
    
    old_index = current_key_indices['cohere']
    old_key_name = COHERE_KEYS[old_index]['name']
    
    for _ in range(len(COHERE_KEYS) - 1):
        current_key_indices['cohere'] = (current_key_indices['cohere'] + 1) % len(COHERE_KEYS)
        entry = COHERE_KEYS[current_key_indices['cohere']]
        
        try:
            new_client = cohere.Client(api_key=entry["key"])
            logger.info(f"🔄 Switched from Cohere {old_key_name} → {entry['name']} key")
            return new_client
        except Exception as e:
            logger.error(f"❌ Cohere {entry['name']} key also failed: {e}")
    
    logger.error(f"❌ All Cohere backup keys exhausted after {old_key_name} failed!")
    return None

def _call_cohere(prompt, client):
    """Internal Cohere API caller with streaming"""
    try:
        response = ""
        last_update = time.time()
        
        stream = client.chat_stream(message=prompt, temperature=0)
        
        for event in stream:
            if event.event_type == "text-generation":
                response += event.text
                
                # Show updates every 0.3s or every 100 chars
                current_time = time.time()
                if (current_time - last_update > 0.3) or (len(response) % 100 == 0):
                    last_update = current_time
        
        return response.strip()
    except Exception as e:
        logger.error(f"Cohere error: {e}")
        raise

# ============= GROQ =============

def setup_groq_model():
    """Initialize Groq with first available key"""
    from groq import Groq
    
    for i, entry in enumerate(GROQ_KEYS):
        try:
            client = Groq(api_key=entry["key"])
            
            # Test the key
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "test"}]
            )
            
            logger.info(f"✅ Using {entry['name']} key")
            current_key_indices['groq'] = i
            return client
        except Exception as e:
            logger.error(f"❌ Failed with {entry['name']}: {e}")
    
    logger.error("❌ All Groq API keys failed!")
    return None

def switch_to_next_groq_key():
    """Switch to next available Groq API key"""
    from groq import Groq
    
    for _ in range(len(GROQ_KEYS) - 1):
        current_key_indices['groq'] = (current_key_indices['groq'] + 1) % len(GROQ_KEYS)
        entry = GROQ_KEYS[current_key_indices['groq']]
        
        try:
            client = Groq(api_key=entry["key"])
            
            # Test the key
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "test"}]
            )
            
            logger.info(f"🔄 Switched to {entry['name']} key")
            return client
        except Exception as e:
            logger.error(f"❌ {entry['name']} key also failed: {e}")
    
    logger.error("❌ All Groq backup keys exhausted!")
    return None

def _call_groq(prompt, client):
    """Internal Groq API caller"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq error: {e}")
        raise

# ============= HUGGINGFACE =============

def setup_huggingface_client():
    """Initialize HuggingFace with first available key"""
    for i, entry in enumerate(HUGGINGFACE_KEYS):
        if entry["key"]:
            logger.info(f"✅ Using {entry['name']} key")
            current_key_indices['huggingface'] = i
            return entry["key"]
    
    logger.error("❌ All HuggingFace API keys failed!")
    return None

def switch_to_next_hf_key():
    """Switch to next available HuggingFace API key"""
    for _ in range(len(HUGGINGFACE_KEYS) - 1):
        current_key_indices['huggingface'] = (current_key_indices['huggingface'] + 1) % len(HUGGINGFACE_KEYS)
        entry = HUGGINGFACE_KEYS[current_key_indices['huggingface']]
        
        if entry["key"]:
            logger.info(f"🔄 Switched to {entry['name']} key")
            return entry["key"]
    
    logger.error("❌ All HuggingFace backup keys exhausted!")
    return None
from huggingface_hub import InferenceClient
def _call_huggingface(prompt, key):
    """Internal HuggingFace API caller"""
    try:
        # import requests
        client = InferenceClient(
            model="Qwen/Qwen2.5-Coder-32B-Instruct",
            token=key
        )

        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        result = response.choices[0].message.content
        
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "").strip()
        elif isinstance(result, dict):
            return result.get("generated_text", "").strip()
        
        return str(result).strip()
    
    except Exception as e:
        logger.error(f"HuggingFace error: {e}")
        raise

# ============= OPENROUTER =============

def setup_openrouter_client():
    """Initialize OpenRouter with first available key"""
    for i, entry in enumerate(OPENROUTER_KEYS):
        if entry["key"]:
            logger.info(f"✅ Using {entry['name']} key")
            current_key_indices['openrouter'] = i
            return entry["key"]
    
    logger.error("❌ All OpenRouter API keys failed!")
    return None

def switch_to_next_or_key():
    """Switch to next available OpenRouter API key"""
    for _ in range(len(OPENROUTER_KEYS) - 1):
        current_key_indices['openrouter'] = (current_key_indices['openrouter'] + 1) % len(OPENROUTER_KEYS)
        entry = OPENROUTER_KEYS[current_key_indices['openrouter']]
        
        if entry["key"]:
            logger.info(f"🔄 Switched to {entry['name']} key")
            return entry["key"]
    
    logger.error("❌ All OpenRouter backup keys exhausted!")
    return None

def _call_openrouter(prompt, key):
    """Internal OpenRouter API caller"""
    try:
        import requests
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}"}
        
        data = {
            "model": "deepseek/deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        raise

# ============= MISTRAL =============

def setup_mistral_client():
    """Initialize Mistral with first available key"""
    for i, entry in enumerate(MISTRAL_KEYS):
        if entry["key"]:
            logger.info(f"✅ Using {entry['name']} key")
            current_key_indices['mistral'] = i
            return entry["key"]
    
    logger.error("❌ All Mistral API keys failed!")
    return None

def switch_to_next_mistral_key():
    """Switch to next available Mistral API key"""
    for _ in range(len(MISTRAL_KEYS) - 1):
        current_key_indices['mistral'] = (current_key_indices['mistral'] + 1) % len(MISTRAL_KEYS)
        entry = MISTRAL_KEYS[current_key_indices['mistral']]
        
        if entry["key"]:
            logger.info(f"🔄 Switched to {entry['name']} key")
            return entry["key"]
    
    logger.error("❌ All Mistral backup keys exhausted!")
    return None

def _call_mistral(prompt, key):
    """Internal Mistral API caller"""
    try:
        import requests
        
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}"}
        
        data = {
            "model": "codestral-latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    except Exception as e:
        logger.error(f"Mistral error: {e}")
        raise


# ============= MAIN CALLER =============

def _is_rate_limit_error(error_msg):
    """Check if error is rate limit related"""
    error_lower = error_msg.lower()
    return any(keyword in error_lower for keyword in [
        'rate limit', 'too many requests', '429', 'quota exceeded',
        'resource_exhausted', 'quota', 'limit exceeded'
    ])

def _show_provider_toast(provider_name):
    """Show toast notification when switching providers"""
    toast_msg = f"🔄 Switched to {provider_name} API"
    logger.info(toast_msg)
    
    try:
        if hasattr(call_ai_model, '_gui_handler'):
            call_ai_model._gui_handler.show_terminal_output(toast_msg, color="cyan")
    except:
        pass

def call_ai_model(prompt, client):
    """
    Universal AI caller with automatic fallback:
    Cohere → Groq → HuggingFace → OpenRouter → Mistral → Cycle back
    """
    global current_provider, groq_client
    
    max_cycles = 2
    attempt = 0
    
    providers = ['cohere', 'groq', 'huggingface', 'openrouter', 'mistral']
    provider_index = providers.index(current_provider)
    
    while attempt < max_cycles:
        try:
            # === COHERE ===
            if current_provider == "cohere":
                try:
                    result = _call_cohere(prompt, client)
                    return result
                except Exception as e:
                    logger.error(f"❌ Cohere error: {type(e).__name__}: {e}")
                    
                    if _is_rate_limit_error(str(e)):
                        new_client = switch_to_next_cohere_key(client)
                        if new_client:
                            try:
                                return _call_cohere(prompt, new_client)
                            except:
                                pass
                    
                    logger.warning("🔄 Cohere exhausted! Switching to Groq...")
                    current_provider = "groq"
                    
                    if not groq_client:
                        groq_client = setup_groq_model()
                    
                    if groq_client:
                        _show_provider_toast("Groq")
                        continue
            
            # === GROQ ===
            elif current_provider == "groq":
                try:
                    return _call_groq(prompt, groq_client)
                except Exception as e:
                    logger.error(f"❌ Groq error: {type(e).__name__}: {e}")
                    
                    if _is_rate_limit_error(str(e)):
                        new_groq = switch_to_next_groq_key()
                        if new_groq:
                            groq_client = new_groq
                            try:
                                return _call_groq(prompt, groq_client)
                            except:
                                pass
                    
                    logger.warning("🔄 Groq exhausted! Switching to HuggingFace...")
                    current_provider = "huggingface"
                    _show_provider_toast("HuggingFace")
                    continue
            
            # === HUGGINGFACE ===
            elif current_provider == "huggingface":
                try:
                    hf_key = HUGGINGFACE_KEYS[current_key_indices['huggingface']]["key"]
                    return _call_huggingface(prompt, hf_key)
                except Exception as e:
                    logger.error(f"❌ HuggingFace error: {type(e).__name__}: {e}")
                    
                    if _is_rate_limit_error(str(e)):
                        new_hf = switch_to_next_hf_key()
                        if new_hf:
                            try:
                                return _call_huggingface(prompt, new_hf)
                            except:
                                pass
                    
                    logger.warning("🔄 HuggingFace exhausted! Switching to OpenRouter...")
                    current_provider = "openrouter"
                    _show_provider_toast("OpenRouter")
                    continue
            
            # === OPENROUTER ===
            elif current_provider == "openrouter":
                try:
                    or_key = OPENROUTER_KEYS[current_key_indices['openrouter']]["key"]
                    return _call_openrouter(prompt, or_key)
                except Exception as e:
                    logger.error(f"❌ OpenRouter error: {type(e).__name__}: {e}")
                    
                    if _is_rate_limit_error(str(e)):
                        new_or = switch_to_next_or_key()
                        if new_or:
                            try:
                                return _call_openrouter(prompt, new_or)
                            except:
                                pass
                    
                    logger.warning("🔄 OpenRouter exhausted! Switching to Mistral...")
                    current_provider = "mistral"
                    _show_provider_toast("Mistral")
                    continue
            
            # === MISTRAL ===
            elif current_provider == "mistral":
                try:
                    mistral_key = MISTRAL_KEYS[current_key_indices['mistral']]["key"]
                    return _call_mistral(prompt, mistral_key)
                except Exception as e:
                    logger.error(f"❌ Mistral error: {type(e).__name__}: {e}")
                    
                    if _is_rate_limit_error(str(e)):
                        new_mistral = switch_to_next_mistral_key()
                        if new_mistral:
                            try:
                                return _call_mistral(prompt, new_mistral)
                            except:
                                pass
                    
                    logger.warning("🔄 Mistral exhausted! Cycling back to Cohere...")
                    current_provider = "cohere"
                    _show_provider_toast("Cohere (retry)")
                    attempt += 1
                    continue
        
        except Exception as e:
            logger.error(f"❌ {current_provider} error: {e}")
            
            # Move to next provider
            provider_index = (provider_index + 1) % len(providers)
            current_provider = providers[provider_index]
            attempt += 1
            
            if attempt >= max_cycles:
                raise Exception(f"❌ All API providers exhausted after {max_cycles} cycles!")
    
    raise Exception("❌ Failed to get response from any AI provider!")