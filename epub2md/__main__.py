"""
Allow running epub2md as a module: python -m epub2md
"""

import sys
from epub2md.cli import main

if __name__ == "__main__":
    sys.exit(main())
