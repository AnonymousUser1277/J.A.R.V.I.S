"""
Core functionality package
"""

from .context_manager import ContextManager
from .notification import ProactiveNotifier
from .auth import authenticate_user, register_face, login_with_face
from .local_server import start_local_server
__all__ = [
    'ContextManager',
    'ProactiveNotifier',
    'authenticate_user',
    'register_face',
    'login_with_face',
    'start_local_server'
]