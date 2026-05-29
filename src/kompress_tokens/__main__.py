"""CLI entry point: kompress_tokens [--threshold FLOAT] [input] [output]

Reads from stdin / writes to stdout if files not provided.
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kompress_tokens",
        description="Compress markdown text with Kompress ONNX INT8 (CPU). "
                    "Frontmatter and fenced code blocks are preserved.",
    )
    parser.add_argument("input", nargs="?", help="Input file (default: stdin)")
    parser.add_argument("output", nargs="?", help="Output file (default: stdout)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        metavar="FLOAT",
        help="Keep-score threshold 0.0–1.0 (default: 0.5; lower = more aggressive)",
    )
    args = parser.parse_args()

    content = (
        open(args.input, encoding="utf-8").read()
        if args.input
        else sys.stdin.read()
    )

    from ._compress import compress_text
    compressed = compress_text(content, threshold=args.threshold)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(compressed)
    else:
        sys.stdout.write(compressed)


if __name__ == "__main__":
    main()
