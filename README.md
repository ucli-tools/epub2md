# EPUB2MD: EPUB to Markdown Converter

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A powerful tool for converting EPUB files to clean, readable Markdown.

## Table of Contents

- [EPUB2MD: EPUB to Markdown Converter](#epub2md-epub-to-markdown-converter)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [Using pip (recommended)](#using-pip-recommended)
    - [Using uv (faster)](#using-uv-faster)
  - [Usage](#usage)
    - [Quick Start - Convert All EPUBs](#quick-start---convert-all-epubs)
    - [Converting a Single File](#converting-a-single-file)
    - [Convert All Files in Current Directory](#convert-all-files-in-current-directory)
    - [Batch Conversion (Different Input/Output Directories)](#batch-conversion-different-inputoutput-directories)
    - [Configuration Options](#configuration-options)
  - [How It Works](#how-it-works)
  - [Examples](#examples)
    - [Convert the God Series](#convert-the-god-series)
    - [Sample Output](#sample-output)
  - [Troubleshooting](#troubleshooting)
    - [Common Issues](#common-issues)
    - [Logging](#logging)
  - [Contributing](#contributing)
  - [License](#license)

## Overview

EPUB2MD converts EPUB ebook files into clean Markdown format, making the content:
- Editable in any text editor
- Compatible with static site generators
- Easy to convert to other formats (PDF via mdtexpdf, DOCX, etc.)
- Version controllable with Git

This tool is designed to work seamlessly with [mdtexpdf](https://github.com/ucli-tools/mdtexpdf) for generating beautiful PDFs from the converted Markdown.

## Features

- **Clean Markdown Output**: Removes HTML artifacts, div blocks, and styling cruft from Pandoc output
- **Metadata Extraction**: Extracts title, author, publisher, and other metadata from EPUB
- **YAML Frontmatter**: Automatically adds frontmatter for static site generators
- **Image Handling**: Extracts and organizes images with optional optimization
- **Batch Processing**: Convert entire directories of EPUB files at once
- **Configurable**: JSON configuration for customizing conversion behavior
- **Robust CLI**: Git-like command structure for ease of use

## Prerequisites

- Python 3.8 or higher
- [Pandoc](https://pandoc.org/installing.html) (for EPUB parsing)

## Installation

### Using pip (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/epub2md.git
cd epub2md

# Create virtual environment and install
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Using uv (faster)

```bash
git clone https://github.com/yourusername/epub2md.git
cd epub2md
uv venv
uv pip install -e .
source .venv/bin/activate.fish  # or activate for bash/zsh
```

## Usage

### Quick Start - Convert All EPUBs

The easiest way to convert all EPUB files in the current directory:

```bash
cd /path/to/your/epubs
epub2md convert --all
```

**Convert all EPUBs including subdirectories:**

```bash
cd /path/to/your/library
epub2md convert --all --recursive
```

This creates a directory for each book with its markdown and images:

```
your_epubs/
├── Book Title 1.epub
├── Book Title 1/           # Created by epub2md
│   ├── Book Title 1.md
│   └── images/
│       └── cover.jpg
├── Book Title 2.epub
├── Book Title 2/           # Created by epub2md
│   ├── Book Title 2.md
│   └── images/
...
```

### Converting a Single File

```bash
# Basic conversion - creates book-name/ directory with .md and images/
epub2md convert book.epub

# Specify custom output path
epub2md convert book.epub custom/path/output.md

# Skip image extraction
epub2md convert book.epub --no-images

# Skip frontmatter generation
epub2md convert book.epub --no-frontmatter

# Optimize/resize images
epub2md convert book.epub --optimize-images
```

### Convert All Files in Current Directory

```bash
# Convert all .epub files in current directory
epub2md convert --all
# or
epub2md convert -a

# Include all subdirectories recursively
epub2md convert --all --recursive
# or
epub2md convert -a -r

# With options
epub2md convert --all --no-frontmatter
```

Output shows progress for each file:

```
Found 32 EPUB file(s) to convert...

✓ 01 - The God Game (The God Series Book 1).epub
  → The God Game (The God Series Book 1)
✓ 02 - The God Factory (The God Series Book 2).epub
  → The God Factory (The God Series Book 2)
...

Conversion complete: 32 succeeded, 0 failed
```

### Batch Conversion (Different Input/Output Directories)

```bash
# Convert all EPUBs from one directory to another
epub2md batch ./epubs ./output

# Include subdirectories
epub2md batch ./epubs ./output --recursive

# With options
epub2md batch ./epubs ./output -r --no-frontmatter
```

### Configuration Options

You can use a JSON configuration file for more control:

```json
{
  "processing": {
    "extract_images": true
  },
  "cleanup": {
    "remove_div_blocks": true,
    "remove_spans": true,
    "fix_headers": true,
    "normalize_whitespace": true,
    "fix_links": true
  },
  "frontmatter": {
    "add": true,
    "custom_fields": {
      "format": "book",
      "toc": true
    }
  },
  "images": {
    "extract_path": "images",
    "optimize": false,
    "max_width": 1200,
    "max_height": 1600
  },
  "pandoc": {
    "extra_args": ["--wrap=none"]
  }
}
```

Use with:

```bash
epub2md convert book.epub --config config.json
```

## How It Works

1. **EPUB Parsing**: Uses Pandoc to extract content from the EPUB's XHTML files
2. **Cleanup Processing**: 
   - Removes `:::` div block markers
   - Cleans up `[]{#...}` span artifacts
   - Fixes header formatting issues
   - Normalizes internal links and anchors
   - Cleans excessive whitespace
3. **Metadata Extraction**: Parses the OPF file for Dublin Core metadata
4. **Image Processing**: Extracts images and updates Markdown references
5. **Frontmatter Generation**: Creates YAML frontmatter from metadata

## Examples

### Convert the God Series

```bash
# Navigate to the series directory
cd ./EPUB_AC_ORDERED/god_series

# Convert ALL books at once
epub2md convert --all

# Or convert a single book
epub2md convert "01 - The God Game (The God Series Book 1).epub"
```

This creates:

```
god_series/
├── 01 - The God Game (The God Series Book 1).epub
├── 01 - The God Game (The God Series Book 1)/
│   ├── 01 - The God Game (The God Series Book 1).md
│   └── images/
│       └── cover.jpg
├── 02 - The God Factory (The God Series Book 2).epub
├── 02 - The God Factory (The God Series Book 2)/
│   ├── 02 - The God Factory (The God Series Book 2).md
│   └── images/
│       └── cover.jpg
...
```

### Sample Output

Input EPUB produces clean Markdown:

```markdown
---
title: "The God Game"
author: "Mike Hockney"
publisher: "Hyperreality Books"
date: "2012"
---

# The God Game

## Quotations

"I will do things no one in the past has dared to do. I will think new 
thoughts, bring new things into being." -- Leonardo da Vinci

...
```

## Troubleshooting

### Common Issues

1. **Pandoc not found**
   ```
   Error: Pandoc not found. Please install Pandoc first.
   ```
   Solution: Install Pandoc from https://pandoc.org/installing.html

2. **Permission denied for images**
   ```
   Error: Permission denied when extracting images
   ```
   Solution: Check write permissions on the output directory

3. **Invalid EPUB file**
   ```
   Error: Invalid EPUB file (not a valid ZIP)
   ```
   Solution: Verify the file is a valid EPUB (EPUB files are ZIP archives)

### Logging

Enable debug logging for more details:

```bash
epub2md convert book.epub --log-level debug
```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

*Part of the document conversion toolchain: EPUB → Markdown (epub2md) → PDF (mdtexpdf)*
