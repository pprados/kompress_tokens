"""Kompress: ML token compression + caveman LLM rewrite for markdown."""

__version__ = "0.2.0"

from ._caveman import AGENTS as CAVEMAN_AGENTS
from ._caveman import DEFAULT_MODELS as CAVEMAN_DEFAULT_MODELS
from ._caveman import LEVELS as CAVEMAN_LEVELS
from ._caveman import caveman_compress
from ._compress import compress_text
from ._protect import split_protected

__all__ = [
    "compress_text",
    "split_protected",
    "caveman_compress",
    "CAVEMAN_LEVELS",
    "CAVEMAN_AGENTS",
    "CAVEMAN_DEFAULT_MODELS",
]
