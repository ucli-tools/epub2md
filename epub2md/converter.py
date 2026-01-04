"""
Core conversion functionality for EPUB2MD.

This module provides the main functions for converting EPUB files to
clean Markdown, including the processing pipeline and batch conversion.
"""

import os
import re
import tempfile
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pypandoc
from bs4 import BeautifulSoup

from epub2md.processors.cleanup import clean_markdown
from epub2md.processors.images import extract_and_process_images
from epub2md.processors.metadata import extract_epub_metadata
from epub2md.utils.logging_utils import get_logger

logger = get_logger(__name__)


def convert_epub_to_markdown(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convert an EPUB file to clean Markdown.
    
    Args:
        input_file: Path to the EPUB file to convert
        output_file: Path for the output Markdown file
        config: Configuration dictionary (optional)
        
    Returns:
        Dict containing statistics about the conversion
    """
    if config is None:
        config = {}
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    # Ensure input file exists and is an .epub file
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if input_path.suffix.lower() != ".epub":
        raise ValueError(f"Input file must be an .epub file: {input_path}")
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Converting {input_path} to {output_path}")
    
    stats = {}
    
    # Step 1: Extract metadata from EPUB
    metadata = extract_epub_metadata(input_path)
    stats["metadata"] = metadata
    
    # Step 2: Set up image extraction directory
    images_dir = config.get("images", {}).get("extract_path", "images")
    if config.get("processing", {}).get("extract_images", True):
        images_dir = output_path.parent / images_dir
        images_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 3: Use Pandoc to convert EPUB to Markdown
    extra_args = config.get("pandoc", {}).get("extra_args", ["--wrap=none"])
    
    # Add image extraction path
    if config.get("processing", {}).get("extract_images", True):
        extra_args.append(f"--extract-media={images_dir}")
    
    # Use markdown_strict for cleaner output, then process
    markdown_content = pypandoc.convert_file(
        str(input_path),
        "markdown",
        format="epub",
        extra_args=extra_args,
    )
    
    # Step 4: Clean up the markdown content
    clean_config = config.get("cleanup", {})
    cleaned_content, cleanup_stats = clean_markdown(
        markdown_content,
        remove_div_blocks=clean_config.get("remove_div_blocks", True),
        remove_spans=clean_config.get("remove_spans", True),
        fix_headers=clean_config.get("fix_headers", True),
        normalize_whitespace=clean_config.get("normalize_whitespace", True),
        fix_links=clean_config.get("fix_links", True),
    )
    stats.update(cleanup_stats)
    
    # Step 5: Process images if extracted
    if config.get("processing", {}).get("extract_images", True) and images_dir.exists():
        image_stats = extract_and_process_images(
            cleaned_content,
            images_dir,
            optimize=config.get("images", {}).get("optimize", False),
            max_width=config.get("images", {}).get("max_width", 1200),
        )
        stats.update(image_stats)
        # Update image paths in content
        cleaned_content = image_stats.get("updated_content", cleaned_content)
    
    # Step 6: Add frontmatter if configured
    if config.get("frontmatter", {}).get("add", True):
        frontmatter = generate_frontmatter(metadata, config.get("frontmatter", {}))
        cleaned_content = frontmatter + "\n\n" + cleaned_content
    
    # Step 7: Write final content
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cleaned_content)
    
    logger.info(f"Conversion completed: {input_path} -> {output_path}")
    
    return {
        "input_file": str(input_path),
        "output_file": str(output_path),
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        **stats,
    }


def generate_frontmatter(metadata: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate YAML frontmatter from metadata."""
    lines = ["---"]
    
    if metadata.get("title"):
        # Escape quotes in title
        title = metadata["title"].replace('"', '\\"')
        lines.append(f'title: "{title}"')
    
    if metadata.get("author"):
        author = metadata["author"].replace('"', '\\"')
        lines.append(f'author: "{author}"')
    
    if metadata.get("publisher"):
        publisher = metadata["publisher"].replace('"', '\\"')
        lines.append(f'publisher: "{publisher}"')
    
    if metadata.get("date"):
        lines.append(f'date: "{metadata["date"]}"')
    
    if metadata.get("language"):
        lines.append(f'language: "{metadata["language"]}"')
    
    if metadata.get("description"):
        description = metadata["description"].replace('"', '\\"').replace("\n", " ")
        lines.append(f'description: "{description}"')
    
    # Add custom fields from config
    for key, value in config.get("custom_fields", {}).items():
        lines.append(f'{key}: "{value}"')
    
    lines.append("---")
    return "\n".join(lines)


def batch_convert(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    config: Optional[Dict[str, Any]] = None,
    recursive: bool = False,
    parallel: bool = True,
) -> Dict[str, Any]:
    """
    Convert multiple EPUB files to Markdown.
    
    Args:
        input_dir: Directory containing EPUB files to convert
        output_dir: Directory for output Markdown files
        config: Configuration dictionary (optional)
        recursive: Whether to recursively process subdirectories
        parallel: Whether to process files in parallel
        
    Returns:
        Dict containing statistics about the batch conversion
    """
    if config is None:
        config = {}
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Ensure input directory exists
    if not input_path.exists() or not input_path.is_dir():
        raise NotADirectoryError(f"Input directory not found: {input_path}")
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all .epub files
    pattern = "**/*.epub" if recursive else "*.epub"
    epub_files = list(input_path.glob(pattern))
    
    if not epub_files:
        logger.warning(f"No .epub files found in {input_path}")
        return {
            "files_processed": 0,
            "files_succeeded": 0,
            "files_failed": 0,
            "results": [],
        }
    
    logger.info(f"Found {len(epub_files)} .epub files to process")
    
    # Prepare conversion tasks
    conversion_tasks = []
    for epub_file in epub_files:
        # Determine relative path from input directory
        rel_path = epub_file.relative_to(input_path)
        
        # Construct output file path with .md extension
        output_file = output_path / rel_path.with_suffix(".md")
        
        # Create parent directories if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        conversion_tasks.append((epub_file, output_file))
    
    results = []
    failed_count = 0
    
    # Process files (sequential only for now due to potential pandoc issues)
    for input_file, output_file in conversion_tasks:
        try:
            result = convert_epub_to_markdown(input_file, output_file, config)
            result["success"] = True
            results.append(result)
            logger.info(f"Converted {input_file} -> {output_file}")
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to convert {input_file}: {str(e)}")
            results.append({
                "input_file": str(input_file),
                "output_file": str(output_file),
                "error": str(e),
                "success": False,
            })
    
    return {
        "files_processed": len(conversion_tasks),
        "files_succeeded": len(conversion_tasks) - failed_count,
        "files_failed": failed_count,
        "results": results,
    }
