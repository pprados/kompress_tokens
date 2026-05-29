# kompress-tokens

Two complementary compression strategies for markdown text:

| Strategy | Engine | Requires |
|----------|--------|----------|
| **caveman** | LLM rewrite (any backend) | API key or CLI |
| **kompress** | Kompress ONNX INT8 ML model | `onnxruntime` |

Frontmatter (`---`) and fenced code blocks (` ``` `) are always preserved unchanged.

## Install

```bash
pip install kompress-tokens                    # kompress only
pip install "kompress-tokens[anthropic]"       # + Anthropic API backend
pip install "kompress-tokens[openai]"          # + OpenAI API backend
pip install "kompress-tokens[all]"             # + all API backends
```

## Caveman backends (auto-detected, with fallback)

| Priority | Backend | Condition |
|----------|---------|-----------|
| 1 | Anthropic API | `ANTHROPIC_API_KEY` set |
| 2 | OpenAI API | `OPENAI_API_KEY` set |
| 3 | Claude CLI | `claude` in PATH |
| 4 | Codex CLI | `codex` in PATH |
| 5 | Gemini CLI | `gemini` in PATH |

Force a specific backend: `--agent=anthropic` / `--agent=claude` / etc.

## CLI

```bash
# Kompress only (default)
kompress_tokens input.md output.md

# Caveman only — auto-detect backend
kompress_tokens --caveman full --no-kompress input.md output.md

# Caveman ultra + kompress (combined pipeline)
kompress_tokens --caveman ultra input.md output.md

# Force Anthropic API, specific model
kompress_tokens --caveman full --agent=anthropic --model=claude-opus-4-8 input.md

# Force OpenAI API
kompress_tokens --caveman lite --agent=openai input.md output.md

# Stdin / stdout
cat input.md | kompress_tokens --caveman full > output.md

# Adjust kompress aggressiveness
kompress_tokens --threshold 0.3 input.md output.md
```

### Caveman levels (from https://github.com/JuliusBrussee/caveman)

| Level | Style | Reduction |
|-------|-------|-----------|
| `lite` | Drop filler, keep articles/full sentences | ~30-40% |
| `full` | Drop articles, fragments OK, short synonyms | ~65% |
| `ultra` | Max compression, arrows (->), abbreviations | ~75%+ |
| `wenyan-lite` | Semi-classical Chinese | ~40-50% |
| `wenyan-full` | Full 文言文 | ~80-90% |
| `wenyan-ultra` | Maximum classical Chinese | highest |

## Python API

```python
from kompress_tokens import compress_text, caveman_compress

# ML token compression (CPU, ONNX)
compressed = compress_text(content, threshold=0.5)

# Caveman rewrite — auto-detect backend
compressed = caveman_compress(content, level="full")

# Force specific backend + model
compressed = caveman_compress(
    content, level="ultra",
    agent="anthropic", model="claude-haiku-4-5-20251001"
)

# Combined pipeline
compressed = compress_text(
    caveman_compress(content, level="ultra")
)
```

## License

Apache-2.0 — prompts adapted from [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman)
