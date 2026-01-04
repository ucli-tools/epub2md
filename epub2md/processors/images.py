"""
Image processing for EPUB2MD.

This module handles extracting, processing, and organizing images
from EPUB files.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Tuple, Union

from epub2md.utils.logging_utils import get_logger

logger = get_logger(__name__)


def extract_and_process_images(
    content: str,
    images_dir: Union[str, Path],
    optimize: bool = False,
    max_width: int = 1200,
    max_height: int = 1600,
) -> Dict[str, Any]:
    """
    Process images extracted from EPUB and update content references.
    
    Args:
        content: Markdown content with image references
        images_dir: Directory where images are extracted
        optimize: Whether to optimize/resize images
        max_width: Maximum width for image optimization
        max_height: Maximum height for image optimization
        
    Returns:
        Dict containing statistics and updated content
    """
    images_dir = Path(images_dir)
    stats = {
        "images_found": 0,
        "images_processed": 0,
        "images_moved": 0,
        "updated_content": content,
    }
    
    if not images_dir.exists():
        logger.warning(f"Images directory does not exist: {images_dir}")
        return stats
    
    # Find all images in the directory (Pandoc may create subdirectories)
    image_files = find_all_images(images_dir)
    stats["images_found"] = len(image_files)
    
    if not image_files:
        # Still fix image paths even if no images found
        content = fix_all_image_paths(content)
        stats["updated_content"] = content
        return stats
    
    # Move all images to the root of images_dir (flatten structure)
    moved_count = flatten_images_to_root(images_dir, image_files)
    stats["images_moved"] = moved_count
    
    # Fix all image paths in content to use simple ./images/filename.jpg format
    content = fix_all_image_paths(content)
    stats["updated_content"] = content
    
    # Optionally optimize images
    if optimize:
        try:
            from PIL import Image
            process_count = optimize_images(images_dir, max_width, max_height)
            stats["images_processed"] = process_count
        except ImportError:
            logger.warning("Pillow not installed, skipping image optimization")
    
    return stats


def find_all_images(directory: Path) -> list[Path]:
    """Find all image files in a directory and subdirectories."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
    images = []
    
    for path in directory.rglob('*'):
        if path.is_file() and path.suffix.lower() in image_extensions:
            images.append(path)
    
    return images


def flatten_images_to_root(images_dir: Path, image_files: list[Path]) -> int:
    """
    Move all images from subdirectories to the images_dir root.
    
    Pandoc often extracts to paths like: images/OEBPS/images/cover.jpg
    We want all images at: images/cover.jpg
    """
    moved_count = 0
    used_names = set()
    
    # First, collect names of images already at root level
    for f in images_dir.iterdir():
        if f.is_file():
            used_names.add(f.name.lower())
    
    for image_path in image_files:
        # Skip if already at root level
        if image_path.parent == images_dir:
            continue
        
        # Determine new filename (avoid conflicts)
        new_name = image_path.name
        base, ext = os.path.splitext(new_name)
        counter = 1
        
        while new_name.lower() in used_names:
            new_name = f"{base}_{counter}{ext}"
            counter += 1
        
        new_path = images_dir / new_name
        used_names.add(new_name.lower())
        
        try:
            shutil.move(str(image_path), str(new_path))
            moved_count += 1
            logger.debug(f"Moved image: {image_path.name} -> {new_path.name}")
        except Exception as e:
            logger.warning(f"Failed to move {image_path}: {e}")
    
    # Clean up empty subdirectories
    cleanup_empty_dirs(images_dir)
    
    return moved_count


def fix_all_image_paths(content: str) -> str:
    """
    Fix all image paths in content to use simple ./images/filename.jpg format.
    
    Handles various path patterns including absolute paths with parentheses:
    - ![](OEBPS/images/cover.jpg)
    - ![](../path/to/Book (Series)/images/cover.jpg)
    - ![](/home/user/project/images/OEBPS/images/cover.jpg)
    - ![alt](path/cover.jpg){#id}
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}
    
    # Find all image references line by line to handle complex paths with parentheses
    lines = content.split('\n')
    fixed_lines = []
    seen_images = set()  # Track unique images to remove duplicates
    last_was_image = False
    last_image_file = None
    
    for line in lines:
        # Check for markdown image pattern at start of line (possibly with whitespace)
        stripped = line.strip()
        
        # Match image pattern - handle paths with parentheses by finding the last )
        if stripped.startswith('!['):
            # Find the ] that closes the alt text
            bracket_end = stripped.find(']')
            if bracket_end > 0 and len(stripped) > bracket_end + 1:
                # Check if followed by (
                if stripped[bracket_end + 1] == '(':
                    # Find the path - it ends at the last ) before any { or end of line
                    rest = stripped[bracket_end + 2:]
                    
                    # Find where the path ends - look for ) that's followed by { or end
                    paren_depth = 1
                    path_end = -1
                    for i, c in enumerate(rest):
                        if c == '(':
                            paren_depth += 1
                        elif c == ')':
                            paren_depth -= 1
                            if paren_depth == 0:
                                path_end = i
                                break
                    
                    if path_end > 0:
                        full_path = rest[:path_end]
                        alt_text = stripped[2:bracket_end]
                        
                        # Extract filename from path
                        path_parts = full_path.replace('\\', '/').split('/')
                        filename = path_parts[-1].strip()
                        
                        # Remove query strings or fragments
                        if '?' in filename:
                            filename = filename.split('?')[0]
                        if '#' in filename:
                            filename = filename.split('#')[0]
                        
                        # Check if it's an image file
                        _, ext = os.path.splitext(filename.lower())
                        
                        if ext in image_extensions and filename:
                            # Check for duplicate consecutive images
                            if last_was_image and last_image_file == filename:
                                # Skip duplicate
                                continue
                            
                            # Skip if we've seen this exact image already at start
                            if filename in seen_images and len(fixed_lines) < 10:
                                continue
                            
                            seen_images.add(filename)
                            fixed_lines.append(f'![{alt_text}](./images/{filename})')
                            last_was_image = True
                            last_image_file = filename
                            continue
        
        # Not an image line
        if stripped:
            last_was_image = False
            last_image_file = None
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def cleanup_empty_dirs(directory: Path) -> None:
    """Remove empty subdirectories recursively."""
    # Collect all subdirectories, deepest first
    subdirs = sorted(
        [d for d in directory.rglob('*') if d.is_dir()],
        key=lambda p: len(p.parts),
        reverse=True
    )
    
    for subdir in subdirs:
        try:
            subdir.rmdir()  # Only removes if empty
            logger.debug(f"Removed empty directory: {subdir}")
        except OSError:
            pass  # Directory not empty, skip


def optimize_images(
    images_dir: Path,
    max_width: int = 1200,
    max_height: int = 1600,
) -> int:
    """
    Optimize images by resizing if too large.
    
    Returns count of images processed.
    """
    try:
        from PIL import Image
    except ImportError:
        return 0
    
    processed = 0
    
    for image_path in find_all_images(images_dir):
        # Only process images at root level (after flattening)
        if image_path.parent != images_dir:
            continue
            
        try:
            with Image.open(image_path) as img:
                # Skip if already small enough
                if img.width <= max_width and img.height <= max_height:
                    continue
                
                # Calculate new size maintaining aspect ratio
                ratio = min(max_width / img.width, max_height / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                
                # Resize and save
                resized = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Determine format
                format_map = {
                    '.jpg': 'JPEG',
                    '.jpeg': 'JPEG',
                    '.png': 'PNG',
                    '.gif': 'GIF',
                    '.webp': 'WEBP',
                }
                img_format = format_map.get(image_path.suffix.lower(), 'PNG')
                
                # Save with optimization
                if img_format == 'JPEG':
                    resized.save(image_path, format=img_format, quality=85, optimize=True)
                else:
                    resized.save(image_path, format=img_format, optimize=True)
                
                processed += 1
                logger.debug(f"Resized image: {image_path.name}")
        
        except Exception as e:
            logger.warning(f"Failed to optimize {image_path}: {e}")
    
    return processed
