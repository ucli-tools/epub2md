"""
Metadata extraction processor for EPUB2MD.

This module handles extracting metadata from EPUB files.
"""

import zipfile
from pathlib import Path
from typing import Any, Dict, Union
from xml.etree import ElementTree as ET

from epub2md.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Common XML namespaces in EPUB/OPF files
NAMESPACES = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
}


def extract_epub_metadata(epub_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extract metadata from an EPUB file.
    
    Args:
        epub_path: Path to the EPUB file
        
    Returns:
        Dict containing extracted metadata (title, author, publisher, etc.)
    """
    epub_path = Path(epub_path)
    metadata = {}
    
    try:
        with zipfile.ZipFile(epub_path, 'r') as epub:
            # Find the OPF file (content.opf or similar)
            opf_path = find_opf_path(epub)
            
            if opf_path:
                opf_content = epub.read(opf_path).decode('utf-8')
                metadata = parse_opf_metadata(opf_content)
            else:
                logger.warning(f"No OPF file found in {epub_path}")
                # Try to extract basic info from filename
                metadata = extract_metadata_from_filename(epub_path.stem)
    
    except zipfile.BadZipFile:
        logger.error(f"Invalid EPUB file (not a valid ZIP): {epub_path}")
        metadata = extract_metadata_from_filename(epub_path.stem)
    except Exception as e:
        logger.error(f"Error extracting metadata from {epub_path}: {e}")
        metadata = extract_metadata_from_filename(epub_path.stem)
    
    return metadata


def find_opf_path(epub: zipfile.ZipFile) -> str | None:
    """Find the path to the OPF file in an EPUB archive."""
    # First, try to find it via container.xml
    try:
        container_content = epub.read("META-INF/container.xml").decode('utf-8')
        root = ET.fromstring(container_content)
        
        # Look for rootfile element
        for rootfile in root.iter():
            if rootfile.tag.endswith('rootfile'):
                opf_path = rootfile.get('full-path')
                if opf_path:
                    return opf_path
    except (KeyError, ET.ParseError):
        pass
    
    # Fallback: look for common OPF file names
    common_names = ['content.opf', 'package.opf', 'OEBPS/content.opf', 'OPS/content.opf']
    for name in common_names:
        if name in epub.namelist():
            return name
    
    # Last resort: find any .opf file
    for filename in epub.namelist():
        if filename.endswith('.opf'):
            return filename
    
    return None


def parse_opf_metadata(opf_content: str) -> Dict[str, Any]:
    """Parse metadata from OPF XML content."""
    metadata = {}
    
    try:
        root = ET.fromstring(opf_content)
        
        # Find metadata section
        metadata_elem = None
        for elem in root.iter():
            if elem.tag.endswith('metadata'):
                metadata_elem = elem
                break
        
        if metadata_elem is None:
            return metadata
        
        # Extract Dublin Core elements
        for child in metadata_elem:
            tag = child.tag.split('}')[-1]  # Remove namespace
            text = child.text
            
            if text:
                text = text.strip()
                
                if tag == 'title':
                    metadata['title'] = text
                elif tag == 'creator':
                    # Handle author (may have role attribute)
                    if 'author' not in metadata:
                        metadata['author'] = text
                    else:
                        metadata['author'] += f", {text}"
                elif tag == 'publisher':
                    metadata['publisher'] = text
                elif tag == 'date':
                    metadata['date'] = text
                elif tag == 'language':
                    metadata['language'] = text
                elif tag == 'description':
                    metadata['description'] = text
                elif tag == 'subject':
                    if 'subjects' not in metadata:
                        metadata['subjects'] = []
                    metadata['subjects'].append(text)
                elif tag == 'identifier':
                    # Could be ISBN or other identifier
                    if 'isbn' in text.lower() or child.get('scheme', '').lower() == 'isbn':
                        metadata['isbn'] = text
                    elif 'identifier' not in metadata:
                        metadata['identifier'] = text
                elif tag == 'rights':
                    metadata['rights'] = text
    
    except ET.ParseError as e:
        logger.error(f"Error parsing OPF XML: {e}")
    
    return metadata


def extract_metadata_from_filename(filename: str) -> Dict[str, Any]:
    """
    Extract basic metadata from filename when OPF parsing fails.
    
    Common patterns:
    - "01 - The God Game (The God Series Book 1)"
    - "Author - Title"
    - "Title by Author"
    """
    metadata = {}
    
    # Try pattern: "## - Title (Series Book #)"
    import re
    pattern1 = re.match(r'^(\d+)\s*-\s*(.+?)(?:\s*\(([^)]+)\))?\s*$', filename)
    if pattern1:
        metadata['title'] = pattern1.group(2).strip()
        if pattern1.group(3):
            metadata['series'] = pattern1.group(3).strip()
        return metadata
    
    # Try pattern: "Author - Title"
    pattern2 = re.match(r'^(.+?)\s*-\s*(.+)$', filename)
    if pattern2:
        metadata['author'] = pattern2.group(1).strip()
        metadata['title'] = pattern2.group(2).strip()
        return metadata
    
    # Fallback: use filename as title
    metadata['title'] = filename
    
    return metadata
