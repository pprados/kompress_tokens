# kompress-tokens

Two complementary compression strategies for markdown text:

| Strategy | Engine | Requires |
|----------|--------|----------|
| **caveman** | Claude CLI rewrite | `claude` CLI |
| **kompress** | Kompress ONNX INT8 ML model | `onnxruntime` |

Frontmatter (`---`) and fenced code blocks (` ``` `) are always preserved unchanged.

## Install

```bash
pip install kompress-tokens
# or
uv add kompress-tokens
```

## CLI

```bash
# Kompress only (default)
kompress_tokens input.md output.md

# Caveman only (lite | full | ultra)
kompress_tokens --caveman full --no-kompress input.md output.md

# Both: caveman then kompress
kompress_tokens --caveman ultra input.md output.md

# Stdin / stdout
cat input.md | kompress_tokens --caveman full > output.md

# Adjust kompress aggressiveness (lower threshold = more aggressive)
kompress_tokens --threshold 0.3 input.md output.md
```

## Python API

```python
from kompress_tokens import compress_text, caveman_compress

# ML token compression (CPU, ONNX)
compressed = compress_text(content, threshold=0.5)

# Caveman rewrite via Claude CLI
compressed = caveman_compress(content, level="full")  # lite | full | ultra

# Combined pipeline
compressed = compress_text(caveman_compress(content, level="ultra"))
```

## How it works

**Caveman** calls the `claude` CLI and asks it to rewrite text in compressed style:
- `lite`: drop articles/filler words; keep all meaning
- `full`: drop hedging/pleasantries; shorter synonyms
- `ultra`: maximum compression; caveman syntax

**Kompress** downloads `chopratejas/kompress-base` (ONNX INT8, ~150 MB) on first use,
scores each token, and drops tokens with score below threshold. Code blocks pass through unchanged.

## License

Apache-2.0
