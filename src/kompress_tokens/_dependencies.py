"""Dependency analysis and ordered compression for template files.

Detects both @filename.md references and {% include %} directives,
builds dependency graph, and compresses in topological order.
"""

import re
from pathlib import Path
from typing import Dict, Set, List


def find_references(content: str) -> Set[str]:
    """Extract @<filename> references from content."""
    pattern = r'@([\w\-]+\.md)'
    return {m.group(1) for m in re.finditer(pattern, content)}


def find_jinja_includes(content: str) -> Set[str]:
    """Extract {% include 'filename' %} or {% include "filename" %} from content."""
    pattern = r'{%\s*include\s+["\']([^"\']+)["\']'
    return {m.group(1) for m in re.finditer(pattern, content)}


def find_all_references(content: str) -> Set[str]:
    """Find both @references and {% include %} directives."""
    refs = find_references(content)
    includes = find_jinja_includes(content)

    # Normalize includes to .template.md for file lookup
    includes = {inc.replace('.md', '.template.md') if inc.endswith('.md') else f"{inc}.template.md"
                for inc in includes}

    return refs | includes


def build_dependency_graph(config_dir: Path, template_files: List[str]) -> Dict[str, Set[str]]:
    """Build dependency graph for all template files."""
    dependencies: Dict[str, Set[str]] = {}

    for tpl_file in template_files:
        path = config_dir / tpl_file
        if not path.exists():
            dependencies[tpl_file] = set()
            continue

        content = path.read_text()
        all_refs = find_all_references(content)

        # Convert .md references to .template.md for actual file lookup
        normalized_refs = set()
        for ref in all_refs:
            if ref.endswith('.template.md'):
                normalized_refs.add(ref)
            else:
                normalized_refs.add(ref.replace('.md', '.template.md'))

        dependencies[tpl_file] = normalized_refs

    return dependencies


def topological_sort(dependencies: Dict[str, Set[str]]) -> List[str]:
    """Return files in dependency order (dependencies first)."""
    sorted_files = []
    visited = set()
    visit_stack = set()

    def visit(file: str):
        if file in visited:
            return
        if file in visit_stack:
            raise ValueError(f"Circular dependency detected: {file}")

        visit_stack.add(file)
        for dep in dependencies.get(file, set()):
            if dep in dependencies:  # Only visit if it's in our set
                visit(dep)
        visit_stack.discard(file)

        visited.add(file)
        sorted_files.append(file)

    for file in dependencies:
        visit(file)

    return sorted_files


def inject_dependencies(content: str, compressed_cache: Dict[str, str]) -> str:
    """Replace @<reference> and {% include %} with compressed content."""
    # Replace @references
    refs = find_references(content)
    for ref in refs:
        ref_template = ref.replace('.md', '.template.md')
        if ref_template in compressed_cache:
            compressed = compressed_cache[ref_template]
            pattern = f"@{re.escape(ref)}"
            content = re.sub(
                pattern,
                f"<!-- BEGIN {ref} -->\n{compressed}\n<!-- END {ref} -->",
                content
            )

    # Replace {% include %} with comment markers
    includes = find_jinja_includes(content)
    for inc in includes:
        inc_template = inc.replace('.md', '.template.md') if inc.endswith('.md') else f"{inc}.template.md"
        if inc_template in compressed_cache:
            compressed = compressed_cache[inc_template]
            # Escape quotes for regex pattern
            pattern = r'{%\s*include\s+["\']' + re.escape(inc) + r'["\']'
            content = re.sub(
                pattern,
                f"<!-- BEGIN {inc} -->\n{compressed}\n<!-- END {inc} -->",
                content
            )

    return content
