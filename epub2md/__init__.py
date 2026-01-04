"""
EPUB2MD: EPUB to Markdown Converter

A tool for converting EPUB files to clean, readable Markdown.
"""

__version__ = "0.1.0"
__author__ = "epub2md contributors"

from epub2md.converter import convert_epub_to_markdown, batch_convert

__all__ = ["convert_epub_to_markdown", "batch_convert", "__version__"]
