"""Kompress: ML token compression + caveman text compression."""

__version__ = "0.1.0"

from ._caveman import LEVELS as CAVEMAN_LEVELS
from ._caveman import caveman_compress
from ._compress import compress_text
from ._protect import split_protected

__all__ = ["compress_text", "split_protected", "caveman_compress", "CAVEMAN_LEVELS"]
