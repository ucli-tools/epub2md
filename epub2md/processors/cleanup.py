"""
Markdown cleanup processor for EPUB2MD.

This module handles cleaning up the raw Pandoc output to produce
clean, readable Markdown without HTML artifacts.
"""

import re
from typing import Dict, Tuple, Any

from epub2md.utils.logging_utils import get_logger

logger = get_logger(__name__)


def clean_markdown(
    content: str,
    remove_div_blocks: bool = True,
    remove_spans: bool = True,
    fix_headers: bool = True,
    normalize_whitespace: bool = True,
    fix_links: bool = True,
) -> Tuple[str, Dict[str, Any]]:
    """
    Clean up raw Pandoc Markdown output from EPUB conversion.
    
    Args:
        content: Raw Markdown content from Pandoc
        remove_div_blocks: Remove ::: div blocks
        remove_spans: Remove []{...} span artifacts
        fix_headers: Clean up header formatting
        normalize_whitespace: Fix excessive whitespace
        fix_links: Clean up internal link artifacts
        
    Returns:
        Tuple of (cleaned content, statistics dict)
    """
    stats = {
        "divs_removed": 0,
        "spans_removed": 0,
        "headers_fixed": 0,
        "links_fixed": 0,
    }
    
    cleaned = content
    
    # Step 1: Remove div blocks (::: {#...} ... :::)
    if remove_div_blocks:
        cleaned, count = remove_div_blocks_from_content(cleaned)
        stats["divs_removed"] = count
    
    # Step 2: Remove empty span references []{#...}
    if remove_spans:
        cleaned, count = remove_span_artifacts(cleaned)
        stats["spans_removed"] = count
    
    # Step 3: Fix headers
    if fix_headers:
        cleaned, count = fix_header_formatting(cleaned)
        stats["headers_fixed"] = count
    
    # Step 4: Clean up internal links and anchors
    if fix_links:
        cleaned, count = fix_link_artifacts(cleaned)
        stats["links_fixed"] = count
    
    # Step 5: Normalize whitespace
    if normalize_whitespace:
        cleaned = normalize_whitespace_content(cleaned)
    
    # Step 6: Final cleanup passes
    cleaned = final_cleanup(cleaned)
    
    logger.info(
        f"Cleanup complete: {stats['divs_removed']} divs, "
        f"{stats['spans_removed']} spans, {stats['headers_fixed']} headers fixed"
    )
    
    return cleaned, stats


def remove_div_blocks_from_content(content: str) -> Tuple[str, int]:
    """
    Remove Pandoc div blocks and extract their content.
    
    Div blocks look like:
    ::: {#id .class style="..."}
    content
    :::
    """
    count = 0
    
    # Pattern to match div opening tags: ::: {#... .class ...}
    div_open_pattern = re.compile(r'^::: \{[^}]*\}\s*$', re.MULTILINE)
    
    # Pattern to match div closing tags: :::
    div_close_pattern = re.compile(r'^:::\s*$', re.MULTILINE)
    
    # Count removals
    count += len(div_open_pattern.findall(content))
    count += len(div_close_pattern.findall(content))
    
    # Remove div markers
    content = div_open_pattern.sub('', content)
    content = div_close_pattern.sub('', content)
    
    return content, count


def remove_span_artifacts(content: str) -> Tuple[str, int]:
    """
    Remove empty span artifacts like []{#id .class}.
    Also handles spans with attributes but no text.
    """
    count = 0
    
    # Pattern: []{#... .class ...}
    empty_span_pattern = re.compile(r'\[\]\{[^}]*\}')
    count = len(empty_span_pattern.findall(content))
    content = empty_span_pattern.sub('', content)
    
    # Pattern: [ ]{#...} (spans with just whitespace)
    whitespace_span_pattern = re.compile(r'\[\s*\]\{[^}]*\}')
    count += len(whitespace_span_pattern.findall(content))
    content = whitespace_span_pattern.sub('', content)
    
    return content, count


def fix_header_formatting(content: str) -> Tuple[str, int]:
    """
    Clean up header formatting issues.
    - Remove inline attributes from headers
    - Fix duplicate hash marks
    - Clean up bold/italic markers inside headers
    """
    count = 0
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        original = line
        
        # Check if it's a header line
        if re.match(r'^#{1,6}\s', line):
            # Remove attribute blocks from headers: {#id .class align="..."}
            header_attr_pattern = re.compile(r'\s*\{[^}]*\}\s*$')
            if header_attr_pattern.search(line):
                line = header_attr_pattern.sub('', line)
                count += 1
            
            # Remove []{#...} spans inside headers
            line = re.sub(r'\[\]\{[^}]*\}', '', line)
            
            # Clean up excessive asterisks in headers (e.g., **text** becomes text)
            # Match header and content
            header_match = re.match(r'^(#{1,6})\s+\*\*(.+?)\*\*\s*$', line)
            if header_match:
                line = f"{header_match.group(1)} {header_match.group(2)}"
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines), count


def fix_link_artifacts(content: str) -> Tuple[str, int]:
    """
    Clean up link artifacts from EPUB internal references.
    - Remove file-based anchors like [text](#index.html_a:4)
    - Clean up image references with weird paths
    """
    count = 0
    
    # Pattern: links to internal HTML anchors (#index.html_xxx)
    internal_link_pattern = re.compile(r'\[([^\]]*)\]\(#[a-zA-Z0-9_]+\.html[^)]*\)')
    matches = internal_link_pattern.findall(content)
    count += len(matches)
    # Keep just the text, remove the link
    content = internal_link_pattern.sub(r'\1', content)
    
    # Pattern: empty links [](#...)
    empty_link_pattern = re.compile(r'\[\]\(#[^)]*\)')
    count += len(empty_link_pattern.findall(content))
    content = empty_link_pattern.sub('', content)
    
    # Fix image paths: ![](OEBPS/images/...) -> ![](images/...)
    oebps_pattern = re.compile(r'!\[([^\]]*)\]\(OEBPS/images/([^)]+)\)')
    count += len(oebps_pattern.findall(content))
    content = oebps_pattern.sub(r'![\1](images/\2)', content)
    
    # Also handle other common EPUB image path patterns
    content = re.sub(r'!\[([^\]]*)\]\(\.\./images/([^)]+)\)', r'![\1](images/\2)', content)
    
    return content, count


def normalize_whitespace_content(content: str) -> str:
    """
    Normalize whitespace in the content.
    - Remove excessive blank lines
    - Fix indentation issues
    - Ensure proper spacing around headers and paragraphs
    """
    # Replace multiple blank lines with double blank line
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # Remove trailing whitespace from lines
    lines = [line.rstrip() for line in content.split('\n')]
    content = '\n'.join(lines)
    
    # Ensure blank line before headers
    content = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', content)
    
    # Remove blank lines at start of content
    content = content.lstrip('\n')
    
    # Ensure single newline at end
    content = content.rstrip('\n') + '\n'
    
    return content


def final_cleanup(content: str) -> str:
    """
    Final cleanup passes for remaining artifacts.
    """
    # Remove lines that are just asterisks (separators like \*\*\*\*\*)
    content = re.sub(r'^\\\*(\\\*)+\s*$', '\n---\n', content, flags=re.MULTILINE)
    
    # Clean up escaped asterisks that should be horizontal rules
    content = re.sub(r'^\*\s*\*\s*\*\s*\*\s*\*\s*$', '\n---\n', content, flags=re.MULTILINE)
    
    # Remove any remaining .was-a-p class references in text
    content = re.sub(r'\.was-a-p', '', content)
    
    # Remove any remaining .k4w-margin references
    content = re.sub(r'\.k4w-margin', '', content)
    
    # Clean up any remaining style attributes in text
    content = re.sub(r'style="[^"]*"', '', content)
    
    # Clean up any remaining align attributes
    content = re.sub(r'align="[^"]*"', '', content)
    
    # Clean up any remaining vertical attributes
    content = re.sub(r'vertical="[^"]*"', '', content)
    
    # Remove HTML tags like <center>, </center>, <div>, etc.
    content = re.sub(r'</?center[^>]*>', '', content)
    content = re.sub(r'</?div[^>]*>', '', content)
    content = re.sub(r'</?span[^>]*>', '', content)
    
    # Remove Pandoc attribute markers from links: {.underline}, {.filepos_src}, etc.
    content = re.sub(r'\{[#.][\w\-_:]+\}', '', content)
    content = re.sub(r'\{\.[a-zA-Z_\-]+\s*\}', '', content)
    
    # Clean up image attributes: ![](path){#id} -> ![](path)
    content = re.sub(r'(!\[[^\]]*\]\([^)]+\))\{[^}]*\}', r'\1', content)
    
    # Remove name="..." and id="..." attributes in remaining HTML
    content = re.sub(r'\s*name="[^"]*"', '', content)
    content = re.sub(r'\s*id="[^"]*"', '', content)
    
    # Clean up underline markers in links: [[text]{.underline}](#link) -> [text](#link)
    content = re.sub(r'\[\[([^\]]+)\]\{\.underline\}\]', r'[\1]', content)
    
    # Remove duplicate images at the start (cover image often appears twice)
    lines = content.split('\n')
    seen_images = set()
    cleaned_lines = []
    for line in lines:
        # Check if line is an image
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', line.strip())
        if img_match:
            img_path = img_match.group(2)
            if img_path in seen_images:
                continue  # Skip duplicate image
            seen_images.add(img_path)
        cleaned_lines.append(line)
    content = '\n'.join(cleaned_lines)
    
    # Remove lines that only contain whitespace and punctuation artifacts
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip lines that are just artifacts
        stripped = line.strip()
        if stripped and not re.match(r'^[\s\-\*\_\#\{\}]+$', stripped):
            cleaned_lines.append(line)
        elif not stripped:
            cleaned_lines.append(line)  # Keep blank lines
    
    content = '\n'.join(cleaned_lines)
    
    # Final whitespace normalization
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content
