"""
Image processing for EPUB2MD.

This module handles extracting, processing, and organizing images
from EPUB files.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

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
        "images_renamed": 0,
        "updated_content": content,
    }
    
    if not images_dir.exists():
        logger.warning(f"Images directory does not exist: {images_dir}")
        return stats
    
    # Find all images in the directory (Pandoc may create subdirectories)
    image_files = find_all_images(images_dir)
    stats["images_found"] = len(image_files)
    
    if not image_files:
        return stats
    
    # Flatten image structure if nested (OEBPS/images/..., etc.)
    content, rename_count = flatten_image_structure(content, images_dir, image_files)
    stats["images_renamed"] = rename_count
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


def flatten_image_structure(
    content: str,
    images_dir: Path,
    image_files: list[Path],
) -> Tuple[str, int]:
    """
    Flatten nested image directories and update content references.
    
    Pandoc often extracts to paths like: images/OEBPS/images/cover.jpg
    We want: images/cover.jpg
    """
    rename_count = 0
    
    for image_path in image_files:
        # Get relative path from images_dir
        try:
            rel_path = image_path.relative_to(images_dir)
        except ValueError:
            continue
        
        # Check if image is in a subdirectory
        if len(rel_path.parts) > 1:
            # Create new flat path
            new_name = sanitize_image_name(image_path.name, rename_count)
            new_path = images_dir / new_name
            
            # Avoid conflicts
            while new_path.exists() and new_path != image_path:
                rename_count += 1
                new_name = sanitize_image_name(image_path.name, rename_count)
                new_path = images_dir / new_name
            
            if new_path != image_path:
                # Move the file
                shutil.move(str(image_path), str(new_path))
                rename_count += 1
                
                # Update content references
                old_ref = str(rel_path).replace('\\', '/')
                new_ref = new_name
                
                # Update markdown image references
                content = content.replace(f"]({old_ref})", f"](images/{new_ref})")
                content = content.replace(f"](images/{old_ref})", f"](images/{new_ref})")
                
                # Also handle OEBPS paths that might be in the content
                content = content.replace(f"](OEBPS/images/{image_path.name})", f"](images/{new_ref})")
    
    # Clean up empty subdirectories
    cleanup_empty_dirs(images_dir)
    
    return content, rename_count


def sanitize_image_name(name: str, index: int = 0) -> str:
    """Sanitize image filename for better organization."""
    # Remove problematic characters
    name = re.sub(r'[^\w\-_\.]', '_', name)
    
    # Add index if needed to avoid conflicts
    if index > 0:
        base, ext = os.path.splitext(name)
        name = f"{base}_{index}{ext}"
    
    return name


def cleanup_empty_dirs(directory: Path) -> None:
    """Remove empty subdirectories."""
    for subdir in list(directory.rglob('*')):
        if subdir.is_dir():
            try:
                subdir.rmdir()  # Only removes if empty
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
