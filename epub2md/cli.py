"""
Command-line interface for EPUB2MD.

Provides a git-like CLI structure for converting EPUB files to Markdown.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

__version__ = "0.1.0"

from epub2md.converter import convert_epub_to_markdown, batch_convert
from epub2md.utils.logging_utils import setup_logging, get_logger


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="epub2md",
        description="Convert EPUB files to clean Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  epub2md convert book.epub                   # Creates book/book.md with book/images/
  epub2md convert book.epub custom.md         # Specify custom output path
  epub2md convert --all                       # Convert ALL EPUBs in current directory
  epub2md batch ./epubs ./output              # Convert all EPUBs in directory
  epub2md batch ./epubs ./output --recursive  # Include subdirectories

Output Structure:
  book.epub  ->  book/
                 ├── book.md
                 └── images/
                     └── (extracted images)
        """,
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"epub2md {__version__}",
    )
    
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level (default: info)",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert EPUB file(s) to Markdown",
    )
    convert_parser.add_argument(
        "input",
        type=str,
        nargs="?",
        help="Path to the EPUB file to convert (not required with --all)",
    )
    convert_parser.add_argument(
        "output",
        type=str,
        nargs="?",
        help="Path for output Markdown file (optional, defaults to input name with .md)",
    )
    convert_parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Convert all EPUB files in the current directory",
    )
    convert_parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip image extraction",
    )
    convert_parser.add_argument(
        "--no-frontmatter",
        action="store_true",
        help="Skip adding YAML frontmatter",
    )
    convert_parser.add_argument(
        "--optimize-images",
        action="store_true",
        help="Optimize/resize extracted images",
    )
    convert_parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON configuration file",
    )
    
    # Batch command
    batch_parser = subparsers.add_parser(
        "batch",
        help="Convert multiple EPUB files in a directory",
    )
    batch_parser.add_argument(
        "input_dir",
        type=str,
        help="Directory containing EPUB files",
    )
    batch_parser.add_argument(
        "output_dir",
        type=str,
        help="Directory for output Markdown files",
    )
    batch_parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Process subdirectories recursively",
    )
    batch_parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip image extraction",
    )
    batch_parser.add_argument(
        "--no-frontmatter",
        action="store_true",
        help="Skip adding YAML frontmatter",
    )
    batch_parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON configuration file",
    )
    
    return parser


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    if not config_path:
        return {}
    
    path = Path(config_path)
    if not path.exists():
        print(f"Warning: Config file not found: {config_path}", file=sys.stderr)
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}", file=sys.stderr)
        return {}


def cmd_convert(args: argparse.Namespace) -> int:
    """Handle the convert command."""
    logger = get_logger(__name__)
    
    # Handle --all flag
    if args.all:
        return cmd_convert_all(args)
    
    # Single file mode requires input
    if not args.input:
        print("Error: Please provide an EPUB file or use --all to convert all EPUBs in current directory", file=sys.stderr)
        return 1
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1
    
    # Determine output path
    # Default: book.epub -> book/book.md (with book/images/)
    if args.output:
        output_path = Path(args.output)
    else:
        # Create a directory named after the book (without extension)
        book_name = input_path.stem
        # Sanitize directory name (remove problematic chars)
        safe_name = sanitize_filename(book_name)
        book_dir = input_path.parent / safe_name
        output_path = book_dir / f"{safe_name}.md"
    
    # Build configuration
    config = load_config(args.config)
    
    if args.no_images:
        config.setdefault("processing", {})["extract_images"] = False
    
    if args.no_frontmatter:
        config.setdefault("frontmatter", {})["add"] = False
    
    if args.optimize_images:
        config.setdefault("images", {})["optimize"] = True
    
    try:
        result = convert_epub_to_markdown(input_path, output_path, config)
        
        print(f"✓ Converted: {result['input_file']}")
        print(f"  Output: {result['output_file']}")
        if result.get("title"):
            print(f"  Title: {result['title']}")
        if result.get("author"):
            print(f"  Author: {result['author']}")
        print(f"  Divs removed: {result.get('divs_removed', 0)}")
        print(f"  Spans removed: {result.get('spans_removed', 0)}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_convert_all(args: argparse.Namespace) -> int:
    """Convert all EPUB files in the current directory."""
    logger = get_logger(__name__)
    
    # Find all .epub files in current directory
    current_dir = Path.cwd()
    epub_files = list(current_dir.glob("*.epub"))
    
    if not epub_files:
        print("No EPUB files found in current directory.", file=sys.stderr)
        return 1
    
    print(f"Found {len(epub_files)} EPUB file(s) to convert...\n")
    
    # Build configuration
    config = load_config(getattr(args, 'config', None))
    
    if args.no_images:
        config.setdefault("processing", {})["extract_images"] = False
    
    if args.no_frontmatter:
        config.setdefault("frontmatter", {})["add"] = False
    
    if args.optimize_images:
        config.setdefault("images", {})["optimize"] = True
    
    succeeded = 0
    failed = 0
    
    for epub_file in sorted(epub_files):
        book_name = epub_file.stem
        safe_name = sanitize_filename(book_name)
        book_dir = epub_file.parent / safe_name
        output_path = book_dir / f"{safe_name}.md"
        
        try:
            result = convert_epub_to_markdown(epub_file, output_path, config)
            print(f"✓ {epub_file.name}")
            if result.get("title"):
                print(f"  → {result['title']}")
            succeeded += 1
        except Exception as e:
            logger.error(f"Failed to convert {epub_file}: {e}")
            print(f"✗ {epub_file.name}: {e}", file=sys.stderr)
            failed += 1
    
    print(f"\nConversion complete: {succeeded} succeeded, {failed} failed")
    
    return 0 if failed == 0 else 1


def sanitize_filename(name: str) -> str:
    """Sanitize a filename for use as directory name."""
    import re
    # Remove or replace problematic characters
    # Keep alphanumeric, spaces, hyphens, underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()
    # If empty, use a default
    if not sanitized:
        sanitized = "output"
    return sanitized


def cmd_batch(args: argparse.Namespace) -> int:
    """Handle the batch command."""
    logger = get_logger(__name__)
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        return 1
    
    # Build configuration
    config = load_config(args.config)
    
    if args.no_images:
        config.setdefault("processing", {})["extract_images"] = False
    
    if args.no_frontmatter:
        config.setdefault("frontmatter", {})["add"] = False
    
    try:
        result = batch_convert(
            input_dir,
            output_dir,
            config=config,
            recursive=args.recursive,
        )
        
        print(f"\nBatch conversion complete:")
        print(f"  Files processed: {result['files_processed']}")
        print(f"  Succeeded: {result['files_succeeded']}")
        print(f"  Failed: {result['files_failed']}")
        
        if result['files_failed'] > 0:
            print("\nFailed files:")
            for r in result['results']:
                if not r.get('success', True):
                    print(f"  - {r['input_file']}: {r.get('error', 'Unknown error')}")
            return 1
        
        return 0
    
    except Exception as e:
        logger.error(f"Batch conversion failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(level=args.log_level.upper())
    
    if not args.command:
        parser.print_help()
        return 0
    
    if args.command == "convert":
        return cmd_convert(args)
    elif args.command == "batch":
        return cmd_batch(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
