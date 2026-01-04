"""
Command-line interface for EPUB2MD.

Provides a git-like CLI structure for converting EPUB files to Markdown.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from epub2md import __version__
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
  epub2md convert book.epub                   # Convert single file
  epub2md convert book.epub output.md         # Specify output file
  epub2md batch ./epubs ./output              # Convert all EPUBs in directory
  epub2md batch ./epubs ./output --recursive  # Include subdirectories
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
        help="Convert a single EPUB file to Markdown",
    )
    convert_parser.add_argument(
        "input",
        type=str,
        help="Path to the EPUB file to convert",
    )
    convert_parser.add_argument(
        "output",
        type=str,
        nargs="?",
        help="Path for output Markdown file (optional, defaults to input name with .md)",
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
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix(".md")
    
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
