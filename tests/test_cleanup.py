"""Tests for the cleanup processor."""

import pytest
from epub2md.processors.cleanup import (
    clean_markdown,
    remove_div_blocks_from_content,
    remove_span_artifacts,
    fix_header_formatting,
    fix_link_artifacts,
)


class TestRemoveDivBlocks:
    """Tests for div block removal."""

    def test_removes_simple_div(self):
        content = """::: {#test}
Hello World
:::"""
        result, count = remove_div_blocks_from_content(content)
        assert ":::" not in result
        assert "Hello World" in result
        assert count == 2

    def test_removes_div_with_classes(self):
        content = """::: {#id .class1 .class2 style="color:red"}
Content here
:::"""
        result, _ = remove_div_blocks_from_content(content)
        assert ":::" not in result
        assert "Content here" in result


class TestRemoveSpanArtifacts:
    """Tests for span artifact removal."""

    def test_removes_empty_spans(self):
        content = "[]{#anchor} Some text"
        result, count = remove_span_artifacts(content)
        assert "[]{" not in result
        assert "Some text" in result
        assert count >= 1

    def test_removes_whitespace_spans(self):
        content = "[ ]{#anchor} More text"
        result, _ = remove_span_artifacts(content)
        assert "]{" not in result


class TestFixHeaderFormatting:
    """Tests for header formatting fixes."""

    def test_removes_header_attributes(self):
        content = "# Title {#id .class align=\"center\"}"
        result, count = fix_header_formatting(content)
        assert "{#" not in result
        assert "# Title" in result
        assert count >= 1

    def test_preserves_header_text(self):
        content = "## Section Title {.section}"
        result, _ = fix_header_formatting(content)
        assert "## Section Title" in result.strip()


class TestFixLinkArtifacts:
    """Tests for link artifact fixes."""

    def test_fixes_internal_html_links(self):
        content = "[Chapter 1](#index.html_123)"
        result, count = fix_link_artifacts(content)
        assert "#index.html" not in result
        assert "Chapter 1" in result
        assert count >= 1

    def test_fixes_image_paths(self):
        content = "![cover](OEBPS/images/cover.jpg)"
        result, _ = fix_link_artifacts(content)
        assert "](images/cover.jpg)" in result


class TestCleanMarkdown:
    """Integration tests for the full cleanup pipeline."""

    def test_full_cleanup(self):
        content = """::: {#wrapper .container}
# Title {#title .header}

[]{#anchor}Some paragraph text.

![](OEBPS/images/img.png)
:::"""
        result, stats = clean_markdown(content)
        
        assert ":::" not in result
        assert "[]{" not in result
        assert "{#" not in result
        assert "Some paragraph text" in result
        assert stats["divs_removed"] > 0
