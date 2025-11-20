"""
Utility decorators
"""

import time
import logging
import functools
from typing import Callable, Any

logger = logging.getLogger(__name__)

def safe_execute(max_retries=3, delay=1.0, exceptions=(Exception,)):
    """
    Decorator that automatically retries a function on failure
    
    Args:
        max_retries: Number of retry attempts (default: 3)
        delay: Seconds to wait between retries (default: 1.0)
        exceptions: Tuple of exceptions to catch (default: all)
    
    Usage:
        @safe_execute(max_retries=3, delay=1.0)
        def my_function():
            # code that might fail
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # Try to execute the function
                    result = func(*args, **kwargs)
                    
                    # If we retried, log success
                    if attempt > 0:
                        logger.info(f"✅ {func.__name__} succeeded on attempt {attempt + 1}")
                    
                    return result
                
                except exceptions as e:
                    last_exception = e
                    
                    # Log the error
                    logger.warning(f"⚠️ {func.__name__} attempt {attempt + 1}/{max_retries} failed: {e}")
                    
                    # Don't wait after the last attempt
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ {func.__name__} failed after {max_retries} attempts")
            
            # All retries failed
            raise last_exception
        
        return wrapper
    return decorator

def timing_decorator(warn_threshold=5.0):
    """
    Decorator to measure function execution time
    
    Args:
        warn_threshold: Warn if execution time exceeds this (seconds)
    
    Usage:
        @timing_decorator(warn_threshold=5.0)
        def slow_function():
            time.sleep(6)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            if elapsed > warn_threshold:
                logger.warning(f"⏱️ {func.__name__} took {elapsed:.2f}s (threshold: {warn_threshold}s)")
            else:
                logger.debug(f"⏱️ {func.__name__} took {elapsed:.2f}s")
            
            return result
        
        return wrapper
    return decorator