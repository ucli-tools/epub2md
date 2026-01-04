# epub2md Examples

This directory contains example output from epub2md conversions.

## Usage Examples

### Convert a Single EPUB

```bash
# Basic conversion
epub2md convert book.epub

# Specify output file
epub2md convert book.epub custom_output.md

# Without images
epub2md convert book.epub --no-images

# Without frontmatter
epub2md convert book.epub --no-frontmatter
```

### Batch Conversion

```bash
# Convert all EPUBs in a directory
epub2md batch ./input_epubs ./output_md

# Recursive (include subdirectories)
epub2md batch ./input_epubs ./output_md --recursive
```

### Example: Converting the God Series

```bash
# Convert a single book
epub2md convert "../EPUB_AC_ORDERED/god_series/01 - The God Game (The God Series Book 1).epub" \
    ./god_game.md

# Batch convert all books
epub2md batch "../EPUB_AC_ORDERED/god_series" ./god_series_md --recursive
```

## Sample Output

After conversion, EPUB files become clean Markdown with YAML frontmatter:

```markdown
---
title: "The God Game (The God Series Book 1)"
author: "Hockney, Mike"
publisher: "Hyperreality Books"
language: "en"
---

# The God Game

**by**

**Mike Hockney**

...content continues...
```

## Image Handling

Images are extracted to an `images/` subdirectory next to the output file:

```
output/
├── book.md
└── images/
    ├── cover.jpg
    └── figure1.png
```

Image references in the Markdown are automatically updated to point to the correct path.
