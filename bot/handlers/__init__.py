"""Handlers package for Mudrex Stats Bot"""

from .listeners import setup_listeners
from .commands import setup_commands
from .admin import setup_admin_commands

__all__ = [
    "setup_listeners",
    "setup_commands",
    "setup_admin_commands",
]
