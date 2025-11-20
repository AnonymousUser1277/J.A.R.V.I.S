"""
External service integrations
"""

from .gmail_integration import GmailIMAP
from .calendar_integration import LocalCalendar

__all__ = [
    'GmailIMAP',
    'LocalCalendar'
]