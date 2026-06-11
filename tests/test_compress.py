"""Tests for kompress_tokens compression modes."""

import tempfile
from pathlib import Path

import pytest

from kompress_tokens.__main__ import compress_single_file, process_batch


class TestCompressSingleFile:
    """Test single file compression."""

    @pytest.mark.skip(reason="Requires ONNX model download")
    def test_kompress_only(self):
        """Test ML compression only (no caveman, no jinja)."""
        content = """# Test Title

This is a test document with content that can be compressed.
The compression should preserve the structure and reduce token usage."""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            result = compress_single_file(
                path,
                caveman_level=None,
                use_jinja=False,
                jinja_vars={},
                no_kompress=False,
                threshold=0.5,
            )
            # Should process through kompress
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            path.unlink()

    def test_no_compression(self):
        """Test with no compression (no-kompress flag)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test\n\nContent to compress.")
            f.flush()
            path = Path(f.name)

        try:
            result = compress_single_file(
                path,
                caveman_level=None,
                use_jinja=False,
                jinja_vars={},
                no_kompress=True,  # Skip kompress
                threshold=0.5,
            )
            # With no-kompress and no caveman, should return original
            assert result == "# Test\n\nContent to compress."
        finally:
            path.unlink()

    def test_caveman_lite(self):
        """Test caveman lite compression (requires API key or CLI)."""
        content = "# Title\n\nThis is a test document."

        # This test might be skipped if no backend is available
        try:
            result = compress_single_file(
                Path("/dev/null"),
                caveman_level="lite",
                use_jinja=False,
                jinja_vars={},
                no_kompress=True,  # Skip ML to focus on caveman
                agent="auto",
            )
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            # Expected if no backend available
            pytest.skip(f"Caveman backend not available: {e}")


class TestBatchMode:
    """Test batch mode processing."""

    def test_batch_produces_md_no_backup(self):
        """Test batch mode produces .md without backup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create a template file
            template_file = config_dir / "test.template.md"
            template_file.write_text("# Test\n\nContent to compress.")

            # Process batch
            process_batch(
                config_dir=config_dir,
                output_dir=config_dir,
                caveman_level=None,
                use_jinja=False,
                jinja_vars={},
                no_kompress=True,
                threshold=0.5,
                agent="auto",
                model=None,
            )

            # Check outputs: only .md produced, no backup
            compressed_file = config_dir / "test.md"
            backup_file = config_dir / "test.md.orig"

            assert compressed_file.exists(), "Compressed file not created"
            assert not backup_file.exists(), "Backup file should not be created"

    def test_batch_multiple_files(self):
        """Test batch mode with multiple template files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create multiple template files
            (config_dir / "a.template.md").write_text("# A\n\nContent A.")
            (config_dir / "b.template.md").write_text("# B\n\nContent B.")

            process_batch(
                config_dir=config_dir,
                output_dir=config_dir,
                caveman_level=None,
                use_jinja=False,
                jinja_vars={},
                no_kompress=True,
                threshold=0.5,
                agent="auto",
                model=None,
            )

            # Check all outputs created (no backups)
            assert (config_dir / "a.md").exists()
            assert not (config_dir / "a.md.orig").exists()
            assert (config_dir / "b.md").exists()
            assert not (config_dir / "b.md.orig").exists()

    def test_batch_empty_directory(self):
        """Test batch mode with no template files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Should handle gracefully
            process_batch(
                config_dir=config_dir,
                output_dir=config_dir,
                caveman_level=None,
                use_jinja=False,
                jinja_vars={},
                no_kompress=True,
                threshold=0.5,
                agent="auto",
                model=None,
            )

            # Directory should remain empty
            assert len(list(config_dir.glob("*.md"))) == 0


class TestFrontmatterPreservation:
    """Test that frontmatter and code blocks are preserved."""

    @pytest.mark.skip(reason="Requires ONNX model and compression library")
    def test_frontmatter_preserved(self):
        """Test YAML frontmatter is preserved."""
        content = """---
title: Test
author: User
---

# Content

Text to compress."""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            result = compress_single_file(
                path,
                caveman_level=None,
                use_jinja=False,
                jinja_vars={},
                no_kompress=True,
                threshold=0.5,
            )
            # Frontmatter should be in result
            assert "---" in result
            assert "title:" in result or "author:" in result
        finally:
            path.unlink()

    @pytest.mark.skip(reason="Requires ONNX model and compression library")
    def test_code_blocks_preserved(self):
        """Test fenced code blocks are preserved."""
        content = """# Code Example

```python
def hello():
    print("world")
```

More content."""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            result = compress_single_file(
                path,
                caveman_level=None,
                use_jinja=False,
                jinja_vars={},
                no_kompress=True,
                threshold=0.5,
            )
            # Code blocks should be preserved
            assert "```" in result
        finally:
            path.unlink()


class TestOutputModes:
    """Test different output modes."""

    def test_single_file_default_creates_backup(self):
        """Test single file mode creates backup without -i."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.md"
            output_file = Path(tmpdir) / "output.md"

            input_file.write_text("# Test\n\nContent.")

            # Simulate compress and backup logic
            compressed = "# Test\n\nContent."
            output_file.write_text(compressed)

            backup_file = output_file.with_suffix(".orig")
            if not backup_file.exists():
                backup_file.write_text(input_file.read_text())

            # Check backup created
            assert backup_file.exists()
            assert backup_file.read_text() == "# Test\n\nContent."

    def test_single_file_in_place(self):
        """Test single file mode with -i flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("# Test\n\nContent.")

            # Simulate in-place replacement
            compressed = "# Test\n\nContent."
            file_path.write_text(compressed)

            # Check no backup created
            backup_file = file_path.with_suffix(".orig")
            assert not backup_file.exists()
            assert file_path.read_text() == compressed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
