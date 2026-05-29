"""CLI entry point for kompress_tokens.

Usage:
  kompress_tokens [options] [input] [output]

Strategies (applied in order when both selected):
  1. caveman  — Claude CLI text rewrite (lite/full/ultra)
  2. kompress — Kompress ONNX INT8 ML compression

Reads from stdin / writes to stdout if files not provided.
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kompress_tokens",
        description=(
            "Compress markdown with caveman and/or Kompress ONNX INT8 (CPU). "
            "Frontmatter and fenced code blocks are always preserved."
        ),
    )
    parser.add_argument("input", nargs="?", help="Input file (default: stdin)")
    parser.add_argument("output", nargs="?", help="Output file (default: stdout)")

    # Caveman options
    parser.add_argument(
        "--caveman",
        choices=["lite", "full", "ultra"],
        metavar="LEVEL",
        default=None,
        help="Enable caveman compression: lite | full | ultra (default: off)",
    )

    # Kompress options
    parser.add_argument(
        "--no-kompress",
        action="store_true",
        help="Skip Kompress ML compression",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        metavar="FLOAT",
        help="Kompress keep-score threshold 0.0–1.0 (default: 0.5; lower = more aggressive)",
    )

    args = parser.parse_args()

    if args.no_kompress and args.caveman is None:
        parser.error("Nothing to do: both --no-kompress and no --caveman level given.")

    content = (
        open(args.input, encoding="utf-8").read()
        if args.input
        else sys.stdin.read()
    )

    # Stage 1: caveman
    if args.caveman:
        from ._caveman import caveman_compress
        content = caveman_compress(content, level=args.caveman)

    # Stage 2: Kompress ML
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
