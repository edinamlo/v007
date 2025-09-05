"""
Parser package initialization.

This module marks the directory as a Python package and can be used
to expose commonly used functions or classes from submodules.
"""

from .parser import parse_filename
from .dir_processor import parse_directory
from .clue_manager import ClueManager
