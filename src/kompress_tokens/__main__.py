"""CLI entry point for kompress_tokens.

Usage:
  kompress_tokens [options] [input] [output]

Strategies (applied in order when both selected):
  1. caveman  -- LLM rewrite (lite/full/ultra/wenyan-*)
  2. kompress -- Kompress ONNX INT8 ML compression (CPU)

Backend auto-detection order for caveman:
  ANTHROPIC_API_KEY -> OPENAI_API_KEY -> claude CLI -> codex CLI -> gemini CLI

Reads from stdin / writes to stdout if files not provided.
"""

import argparse
import sys


def main() -> None:
    from ._caveman import AGENTS, LEVELS

    parser = argparse.ArgumentParser(
        prog="kompress_tokens",
        description=(
            "Compress markdown with caveman LLM rewrite and/or Kompress ONNX INT8 (CPU). "
            "Frontmatter and fenced code blocks are always preserved."
        ),
    )
    parser.add_argument("input", nargs="?", help="Input file (default: stdin)")
    parser.add_argument("output", nargs="?", help="Output file (default: stdout)")

    # Caveman options
    cav = parser.add_argument_group("caveman options")
    cav.add_argument(
        "--caveman",
        choices=list(LEVELS),
        metavar="LEVEL",
        default=None,
        help="Enable caveman compression: " + " | ".join(LEVELS) + " (default: off)",
    )
    cav.add_argument(
        "--agent",
        choices=list(AGENTS),
        default="auto",
        help=(
            "LLM backend for caveman (default: auto). "
            "auto tries: ANTHROPIC_API_KEY -> OPENAI_API_KEY -> claude -> codex -> gemini"
        ),
    )
    cav.add_argument(
        "--model",
        default=None,
        metavar="MODEL_ID",
        help="Override default model for anthropic/openai backends",
    )

    # Kompress options
    kmp = parser.add_argument_group("kompress options")
    kmp.add_argument(
        "--no-kompress",
        action="store_true",
        help="Skip Kompress ML compression",
    )
    kmp.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        metavar="FLOAT",
        help="Kompress keep-score threshold 0.0-1.0 (default: 0.5; lower = more aggressive)",
    )

    args = parser.parse_args()

    if args.no_kompress and args.caveman is None:
        parser.error("Nothing to do: --no-kompress given but no --caveman level.")

    content = (
        open(args.input, encoding="utf-8").read()
        if args.input
        else sys.stdin.read()
    )

    # Stage 1: caveman LLM rewrite
    if args.caveman:
        from ._caveman import caveman_compress
        content = caveman_compress(content, level=args.caveman, agent=args.agent, model=args.model)

    # Stage 2: Kompress ML token compression
    if not args.no_kompress:
        from ._compress import compress_text
        content = compress_text(content, threshold=args.threshold)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        sys.stdout.write(content)


if __name__ == "__main__":
    main()
