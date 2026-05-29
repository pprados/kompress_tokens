"""Kompress ONNX INT8 compression engine (CPU-only)."""

from __future__ import annotations

from typing import Any

from ._protect import split_protected

_MODEL_ID = "chopratejas/kompress-base"
_TOKENIZER_ID = "answerdotai/ModernBERT-base"
_CHUNK_WORDS = 350
_MIN_WORDS = 10

_session: Any = None
_tokenizer: Any = None


def _load() -> tuple[Any, Any]:
    global _session, _tokenizer
    if _session is None:
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        from transformers import AutoTokenizer

        onnx_path = hf_hub_download(_MODEL_ID, "onnx/kompress-int8.onnx")
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 4
        _session = ort.InferenceSession(onnx_path, opts, providers=["CPUExecutionProvider"])
        _tokenizer = AutoTokenizer.from_pretrained(_TOKENIZER_ID)
    return _session, _tokenizer


def _compress_chunk(words: list[str], session: Any, tokenizer: Any, threshold: float) -> list[str]:
    import numpy as np

    enc = tokenizer(
        words,
        is_split_into_words=True,
        truncation=True,
        max_length=512,
        padding=True,
        return_tensors="np",
    )
    scores = session.run(
        ["final_scores"],
        {
            "input_ids": enc["input_ids"].astype(np.int64),
            "attention_mask": enc["attention_mask"].astype(np.int64),
        },
    )[0][0]
    word_ids = enc.word_ids(batch_index=0)
    kept: set[int] = set()
    for idx, wid in enumerate(word_ids):
        if wid is not None and float(scores[idx]) > threshold:
            kept.add(wid)
    return [words[i] for i in sorted(kept)]


def compress_text(content: str, threshold: float = 0.5) -> str:
    """Compress markdown text with Kompress, preserving frontmatter and code blocks."""
    session, tokenizer = _load()

    def _compress(text: str) -> str:
        words = text.split()
        if len(words) < _MIN_WORDS:
            return text
        kept: list[str] = []
        for i in range(0, len(words), _CHUNK_WORDS):
            kept.extend(_compress_chunk(words[i : i + _CHUNK_WORDS], session, tokenizer, threshold))
        return " ".join(kept) if kept else text

    parts = []
    for text, protected in split_protected(content):
        parts.append(text if protected else _compress(text))
    return "".join(parts)
