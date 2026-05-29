"""Caveman compression via Claude CLI."""

from __future__ import annotations

import subprocess

LEVELS = ("lite", "full", "ultra")

_PROMPT_TEMPLATE = """\
Rewrite the following text in caveman mode (level: {level}).
Output ONLY the rewritten text. No explanations, no meta-commentary.
Rules by level:
- lite: drop articles/filler words; fragments OK; keep all meaning
- full: drop hedging/pleasantries; shorter synonyms; tighter phrases
- ultra: maximum compression; caveman syntax; every word earns its place

TEXT:
{content}"""


def caveman_compress(content: str, level: str = "full") -> str:
    """Compress text with Claude CLI caveman mode.

    Args:
        content: Text to compress.
        level: One of 'lite', 'full', 'ultra'.

    Raises:
        ValueError: Unknown level.
        RuntimeError: Claude CLI not found or returned non-zero.
    """
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}, got {level!r}")

    prompt = _PROMPT_TEMPLATE.format(level=level, content=content)
    result = subprocess.run(
        [
            "claude",
            "--dangerously-skip-permissions",
            "--settings", '{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true}}',
            "-c", prompt,
        ],
        input=content,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI failed: {result.stderr}")
    return result.stdout
