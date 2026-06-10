"""Caveman compression with multiple LLM backends and auto-detection.

Backend priority (auto mode):
  1. ANTHROPIC_API_KEY  -> Anthropic API  (claude-haiku-4-5)
  2. OPENAI_API_KEY     -> OpenAI API     (gpt-4o-mini)
  3. claude in PATH     -> Claude CLI
  4. codex  in PATH     -> OpenAI Codex CLI
  5. gemini in PATH     -> Gemini CLI

Prompts adapted from https://github.com/JuliusBrussee/caveman
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Literal

LEVELS = ("lite", "full", "ultra")
AGENTS = ("auto", "anthropic", "openai", "claude", "codex", "gemini")
Agent = Literal["auto", "anthropic", "openai", "claude", "codex", "gemini"]

DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
}

# Prompts adapted from https://github.com/JuliusBrussee/caveman
_SYSTEM_PROMPT = (
    "You are a text compression tool. "
    "Rewrite the given text in caveman compression style. "
    "Output ONLY the rewritten text. No explanations, no meta-commentary. "
    "Preserve exactly: code blocks (```...```), inline code (`...`), "
    "URLs, file paths, commands, technical terms, version numbers, proper nouns."
)

_LEVEL_RULES: dict[str, str] = {
    "lite": (
        "Compression level: lite.\n"
        "Drop filler words (just/really/basically/actually/simply), "
        "pleasantries, hedging language.\n"
        "Keep articles and complete sentences.\n"
        "Target: ~30-40% token reduction."
    ),
    "full": (
        "Compression level: full (default caveman).\n"
        "Drop articles (a/an/the). Fragments acceptable.\n"
        "Use short synonyms: big not extensive, fix not 'implement a solution for'.\n"
        "Pattern: [thing] [action] [reason]. [next step].\n"
        "Target: ~65% token reduction."
    ),
    "ultra": (
        "Compression level: ultra.\n"
        "Maximum compression. Every word earns its place.\n"
        "Abbreviations and contractions OK. Arrows for causality (->).\n"
        "Single words or short phrases for ideas. Minimal punctuation.\n"
        "Target: ~75%+ token reduction."
    ),
}


def _user_prompt(content: str, level: str) -> str:
    return f"{_LEVEL_RULES[level]}\n\nTEXT:\n{content}"


def _compress_anthropic(content: str, level: str, model: str) -> str:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed: pip install anthropic")
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=max(512, len(content.split()) * 3),
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _user_prompt(content, level)}],
    )
    return msg.content[0].text


def _compress_openai(content: str, level: str, model: str) -> str:
    try:
        import openai
    except ImportError:
        raise RuntimeError("openai package not installed: pip install openai")
    client = openai.OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(content, level)},
        ],
    )
    return resp.choices[0].message.content or content


def _compress_claude_cli(content: str, level: str) -> str:
    if not shutil.which("claude"):
        raise RuntimeError("claude CLI not found in PATH")
    prompt = f"{_SYSTEM_PROMPT}\n\n{_user_prompt(content, level)}"
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
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI exited {result.returncode}: {result.stderr.strip()}")
    return result.stdout


def _compress_codex_cli(content: str, level: str) -> str:
    if not shutil.which("codex"):
        raise RuntimeError("codex CLI not found in PATH")
    prompt = f"{_SYSTEM_PROMPT}\n\n{_user_prompt(content, level)}"
    result = subprocess.run(
        ["codex", "--quiet", prompt],
        text=True,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"codex CLI exited {result.returncode}: {result.stderr.strip()}")
    return result.stdout


def _compress_gemini_cli(content: str, level: str) -> str:
    if not shutil.which("gemini"):
        raise RuntimeError("gemini CLI not found in PATH")
    prompt = f"{_SYSTEM_PROMPT}\n\n{_user_prompt(content, level)}"
    result = subprocess.run(
        ["gemini", "-p", prompt],
        text=True,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gemini CLI exited {result.returncode}: {result.stderr.strip()}")
    return result.stdout


def _auto_chain() -> list[str]:
    """Return available agents in priority order."""
    chain: list[str] = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        chain.append("anthropic")
    if os.environ.get("OPENAI_API_KEY"):
        chain.append("openai")
    if shutil.which("claude"):
        chain.append("claude")
    if shutil.which("codex"):
        chain.append("codex")
    if shutil.which("gemini"):
        chain.append("gemini")
    return chain


def _dispatch(content: str, level: str, agent: str, model: str | None) -> str:
    if agent == "anthropic":
        return _compress_anthropic(content, level, model or DEFAULT_MODELS["anthropic"])
    if agent == "openai":
        return _compress_openai(content, level, model or DEFAULT_MODELS["openai"])
    if agent == "claude":
        return _compress_claude_cli(content, level)
    if agent == "codex":
        return _compress_codex_cli(content, level)
    if agent == "gemini":
        return _compress_gemini_cli(content, level)
    raise ValueError(f"Unknown agent: {agent!r}")


def caveman_compress(
    content: str,
    level: str = "full",
    agent: str = "auto",
    model: str | None = None,
) -> str:
    """Compress text using caveman style via the best available LLM backend.

    Args:
        content: Text to compress.
        level:   lite / full / ultra
        agent:   auto | anthropic | openai | claude | codex | gemini
                 'auto' tries available backends in priority order with fallback.
        model:   Override default model (anthropic/openai backends only).
    """
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}, got {level!r}")
    if agent not in AGENTS:
        raise ValueError(f"agent must be one of {AGENTS}, got {agent!r}")

    if agent != "auto":
        return _dispatch(content, level, agent, model)

    chain = _auto_chain()
    if not chain:
        raise RuntimeError(
            "No LLM agent available. "
            "Set ANTHROPIC_API_KEY or OPENAI_API_KEY, "
            "or install claude / codex / gemini CLI."
        )

    errors: list[str] = []
    for a in chain:
        try:
            return _dispatch(content, level, a, model)
        except Exception as exc:
            errors.append(f"  {a}: {exc}")

    raise RuntimeError("All agents failed:\n" + "\n".join(errors))
