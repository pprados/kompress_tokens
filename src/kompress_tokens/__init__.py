"""Kompress: ML token compression via chopratejas/kompress-base ONNX INT8, CPU-only."""

__version__ = "0.1.0"

from ._compress import compress_text
from ._protect import split_protected

__all__ = ["compress_text", "split_protected"]
