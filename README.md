# kompress-tokens

ML token compression for markdown using [Kompress](https://huggingface.co/chopratejas/kompress-base) ONNX INT8, CPU-only.

Frontmatter (`---`) and fenced code blocks (` ``` `) are always preserved unchanged.

## Install

```bash
pip install kompress-tokens
# or
uv add kompress-tokens
```

## CLI

```bash
# File to file
kompress_tokens input.md output.md

# stdin / stdout
cat input.md | kompress_tokens > output.md

# Adjust aggressiveness (default 0.5; lower = more aggressive)
kompress_tokens --threshold 0.3 input.md output.md
```

## Python API

```python
from kompress_tokens import compress_text

compressed = compress_text(content, threshold=0.5)
```

## How it works

1. Splits content into protected regions (frontmatter, code blocks) and text segments
2. Each text segment is tokenized and scored by `chopratejas/kompress-base` (ModernBERT)
3. Tokens with score > threshold are kept; others are dropped
4. Protected regions pass through unchanged

The ONNX INT8 model downloads automatically from HuggingFace on first use (~150 MB).

## License

Apache-2.0
