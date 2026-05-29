"""Split markdown content into protected and compressible segments."""

import re


def split_protected(content: str) -> list[tuple[str, bool]]:
    """Return list of (text, is_protected) segments.

    Protected (passed through unchanged):
      - YAML frontmatter: ---\\n...\\n--- at file start
      - Fenced code blocks: ```...```
    """
    segments: list[tuple[str, bool]] = []
    pos = 0

    fm = re.match(r'^---\n.*?\n---\n', content, re.DOTALL)
    if fm:
        segments.append((fm.group(), True))
        pos = fm.end()

    base = pos
    for match in re.finditer(r'```[^\n]*\n.*?```', content[base:], re.DOTALL):
        start = base + match.start()
        end = base + match.end()
        if start > pos:
            segments.append((content[pos:start], False))
        segments.append((match.group(), True))
        pos = end

    if pos < len(content):
        segments.append((content[pos:], False))

    return segments
