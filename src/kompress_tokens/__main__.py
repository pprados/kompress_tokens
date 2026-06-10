"""CLI entry point for kompress_tokens.

Usage:
  kompress_tokens [options] [input] [output]
  kompress_tokens --batch [options] <config_dir> [output_dir]

Strategies (applied in order when both selected):
  0. jinja   -- Jinja2 template rendering (opt-in)
  1. caveman -- LLM rewrite (lite/full/ultra)
  2. kompress -- Kompress ONNX INT8 ML compression (CPU)

Batch mode:
  Compresses all .template.md files with dependency analysis and injection.
  Supports @references and {% include %} directives.

Backend auto-detection order for caveman:
  ANTHROPIC_API_KEY -> OPENAI_API_KEY -> claude CLI -> codex CLI -> gemini CLI

Reads from stdin / writes to stdout if files not provided.
"""

import argparse
import sys
from pathlib import Path


def render_jinja(content: str, template_file: str, jinja_vars: dict = None) -> str:
    """Render Jinja2 template string or file."""
    if jinja_vars is None:
        jinja_vars = {}
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        raise RuntimeError("jinja2 not installed. Run: uv add jinja2")

    import os
    template_dir = os.path.dirname(os.path.abspath(template_file))
    template_name = os.path.basename(template_file)
    env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)
    tmpl = env.get_template(template_name)
    return tmpl.render(**jinja_vars)


def compress_single_file(
    path: Path,
    caveman_level: str = None,
    use_jinja: bool = False,
    jinja_vars: dict = None,
    no_kompress: bool = False,
    threshold: float = 0.5,
    agent: str = "auto",
    model: str = None,
) -> str:
    """Compress a single file."""
    if jinja_vars is None:
        jinja_vars = {}

    content = path.read_text()

    # Stage 0: Jinja2 rendering
    if use_jinja:
        content = render_jinja(content, str(path), jinja_vars)

    # Stage 1: caveman compression
    if caveman_level:
        from ._caveman import caveman_compress
        content = caveman_compress(content, level=caveman_level, agent=agent, model=model)

    # Stage 2: Kompress ML compression
    if not no_kompress:
        from ._compress import compress_text
        content = compress_text(content, threshold=threshold)

    return content


def process_batch(
    config_dir: Path,
    output_dir: Path,
    caveman_level: str = None,
    use_jinja: bool = False,
    jinja_vars: dict = None,
    no_kompress: bool = False,
    threshold: float = 0.5,
    agent: str = "auto",
    model: str = None,
) -> None:
    """Process templates in batch with dependency analysis."""
    from ._dependencies import build_dependency_graph, topological_sort, inject_dependencies

    if jinja_vars is None:
        jinja_vars = {}

    # Find all template files
    template_files = sorted([f.name for f in config_dir.glob('*.template.md')])

    if not template_files:
        print(f"No .template.md files found in {config_dir}")
        return

    print(f"Found {len(template_files)} template files\n")

    # Build dependency graph
    print("Building dependency graph...")
    dependencies = build_dependency_graph(config_dir, template_files)

    print("Dependencies:")
    for tpl, deps in dependencies.items():
        if deps:
            print(f"  {tpl} depends on: {', '.join(sorted(deps))}")

    # Topological sort
    print("\nDetermining compression order...")
    sorted_files = topological_sort(dependencies)
    print(f"Order: {' → '.join(sorted_files)}\n")

    # Compress in order
    print("Compressing templates:")
    compressed_cache = {}
    results = {}

    for template_file in sorted_files:
        try:
            path = config_dir / template_file
            if not path.exists():
                print(f"  ✗ File not found: {template_file}")
                continue

            print(f"  {template_file}...", end=" ", flush=True)

            # Compress the file
            compressed = compress_single_file(
                path,
                caveman_level=caveman_level,
                use_jinja=use_jinja,
                jinja_vars=jinja_vars,
                no_kompress=no_kompress,
                threshold=threshold,
                agent=agent,
                model=model,
            )

            # Inject dependencies
            compressed = inject_dependencies(compressed, compressed_cache)

            # Store in cache
            compressed_cache[template_file] = compressed
            results[template_file] = compressed

            # Write output
            output_file = template_file.replace('.template.md', '.md')
            output_path = output_dir / output_file
            output_path.write_text(compressed)

            print(f"✓ → {output_file}")

        except Exception as e:
            print(f"✗ Error: {e}")
            raise

    print(f"\n✓ All templates compressed successfully")


def main() -> None:
    from ._caveman import AGENTS, LEVELS

    parser = argparse.ArgumentParser(
        prog="kompress_tokens",
        description=(
            "Compress markdown with Jinja2 rendering, caveman LLM rewrite, and/or Kompress ONNX INT8 (CPU). "
            "Frontmatter and fenced code blocks are always preserved."
        ),
    )

    # Batch mode
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: compress all .template.md files with dependency analysis"
    )

    parser.add_argument("input", nargs="?", help="Input file or directory (default: stdin)")
    parser.add_argument("output", nargs="?", help="Output file or directory (default: stdout/input dir)")

    # Jinja options
    jinja = parser.add_argument_group("jinja options")
    jinja.add_argument(
        "--jinja",
        action="store_true",
        default=False,
        help="Enable Jinja2 template rendering (default: off)",
    )
    jinja.add_argument(
        "--jinja-var",
        action="append",
        dest="jinja_vars",
        metavar="KEY=VALUE",
        help="Jinja2 variable to inject (repeatable, implies --jinja)",
    )

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

    if args.no_kompress and args.caveman is None and not args.jinja:
        parser.error("Nothing to do: --no-kompress given but no --caveman level or --jinja.")

    # Parse Jinja2 variables
    jinja_vars = {}
    if args.jinja_vars:
        for var_str in args.jinja_vars:
            if '=' not in var_str:
                parser.error(f"Invalid Jinja variable format: {var_str}. Expected KEY=VALUE")
            key, value = var_str.split('=', 1)
            jinja_vars[key] = value

    # --jinja-var implies --jinja
    use_jinja = args.jinja or bool(jinja_vars)

    # Batch mode
    if args.batch:
        if not args.input:
            parser.error("--batch requires input directory")
        config_dir = Path(args.input)
        if not config_dir.exists():
            print(f"Config directory not found: {config_dir}")
            sys.exit(1)
        output_dir = Path(args.output) if args.output else config_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            process_batch(
                config_dir=config_dir,
                output_dir=output_dir,
                caveman_level=args.caveman,
                use_jinja=use_jinja,
                jinja_vars=jinja_vars,
                no_kompress=args.no_kompress,
                threshold=args.threshold,
                agent=args.agent,
                model=args.model,
            )
        except Exception as e:
            print(f"\n✗ Failed: {e}")
            sys.exit(1)
        return

    # Single file mode
    # Read input
    if args.input:
        content = open(args.input, encoding="utf-8").read()
    else:
        content = sys.stdin.read()

    # Stage 0: Jinja2 rendering
    if use_jinja:
        if not args.input:
            parser.error("--jinja requires input file (stdin not supported for Jinja2)")
        content = render_jinja(content, args.input, jinja_vars)

    # Stage 1: caveman LLM rewrite
    if args.caveman:
        from ._caveman import caveman_compress
        content = caveman_compress(content, level=args.caveman, agent=args.agent, model=args.model)

    # Stage 2: Kompress ML token compression
    if not args.no_kompress:
        from ._compress import compress_text
        content = compress_text(content, threshold=args.threshold)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        sys.stdout.write(content)


if __name__ == "__main__":
    main()
