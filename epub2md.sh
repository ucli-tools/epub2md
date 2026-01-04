#!/bin/bash
#
# epub2md.sh - EPUB to Markdown converter wrapper script
#
# This script provides install/uninstall functionality and wraps the Python module.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="/usr/local/share/epub2md"
BIN_DIR="/usr/local/bin"
SCRIPT_NAME="epub2md"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

show_help() {
    echo "epub2md - EPUB to Markdown Converter"
    echo ""
    echo "Usage: epub2md <command> [options]"
    echo ""
    echo "Commands:"
    echo "  convert <file.epub> [output.md]   Convert a single EPUB file"
    echo "  batch <input_dir> <output_dir>    Convert all EPUBs in a directory"
    echo "  install                           Install epub2md system-wide"
    echo "  uninstall                         Remove epub2md from system"
    echo "  check                             Check prerequisites"
    echo "  help                              Show this help message"
    echo ""
    echo "Options for convert:"
    echo "  --no-images           Skip image extraction"
    echo "  --no-frontmatter      Skip YAML frontmatter generation"
    echo "  --optimize-images     Optimize/resize extracted images"
    echo "  --log-level LEVEL     Set logging level (debug, info, warning, error)"
    echo ""
    echo "Options for batch:"
    echo "  -r, --recursive       Process subdirectories recursively"
    echo "  --no-images           Skip image extraction"
    echo "  --no-frontmatter      Skip YAML frontmatter generation"
    echo ""
    echo "Examples:"
    echo "  epub2md convert book.epub"
    echo "  epub2md convert book.epub output.md"
    echo "  epub2md batch ./epubs ./output --recursive"
    echo ""
}

check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"
    
    local missing=0
    
    # Check Python
    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}✓ Python 3 is installed${NC}"
    else
        echo -e "${RED}✗ Python 3 is not installed${NC}"
        missing=1
    fi
    
    # Check Pandoc
    if command -v pandoc &> /dev/null; then
        echo -e "${GREEN}✓ Pandoc is installed${NC}"
    else
        echo -e "${RED}✗ Pandoc is not installed${NC}"
        echo -e "${YELLOW}  Install with: sudo apt install pandoc${NC}"
        missing=1
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
        echo -e "${GREEN}✓ pip is installed${NC}"
    else
        echo -e "${RED}✗ pip is not installed${NC}"
        missing=1
    fi
    
    if [ $missing -eq 1 ]; then
        echo -e "${RED}Please install missing prerequisites.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}All prerequisites are installed!${NC}"
    return 0
}

do_install() {
    echo -e "${BLUE}Installing epub2md...${NC}"
    
    # Check prerequisites first
    if ! check_prerequisites; then
        exit 1
    fi
    
    # Create installation directory
    echo -e "${BLUE}Creating installation directory...${NC}"
    sudo mkdir -p "$INSTALL_DIR"
    
    # Copy Python package
    echo -e "${BLUE}Copying Python package...${NC}"
    sudo cp -r "$SCRIPT_DIR/epub2md" "$INSTALL_DIR/"
    sudo cp "$SCRIPT_DIR/pyproject.toml" "$INSTALL_DIR/"
    sudo cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/"
    
    # Create virtual environment and install dependencies
    echo -e "${BLUE}Setting up Python virtual environment...${NC}"
    sudo python3 -m venv "$INSTALL_DIR/.venv"
    sudo "$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
    sudo "$INSTALL_DIR/.venv/bin/pip" install -e "$INSTALL_DIR"
    
    # Create wrapper script in /usr/local/bin
    echo -e "${BLUE}Creating command wrapper...${NC}"
    sudo tee "$BIN_DIR/$SCRIPT_NAME" > /dev/null << 'WRAPPER'
#!/bin/bash
# epub2md wrapper - calls the Python module
INSTALL_DIR="/usr/local/share/epub2md"
exec "$INSTALL_DIR/.venv/bin/python" -m epub2md "$@"
WRAPPER
    
    sudo chmod +x "$BIN_DIR/$SCRIPT_NAME"
    
    echo -e "${GREEN}✓ epub2md installed successfully!${NC}"
    echo -e "${BLUE}You can now use: epub2md convert <file.epub>${NC}"
}

do_uninstall() {
    echo -e "${BLUE}Uninstalling epub2md...${NC}"
    
    # Remove wrapper script
    if [ -f "$BIN_DIR/$SCRIPT_NAME" ]; then
        sudo rm "$BIN_DIR/$SCRIPT_NAME"
        echo -e "${GREEN}✓ Removed $BIN_DIR/$SCRIPT_NAME${NC}"
    fi
    
    # Remove installation directory
    if [ -d "$INSTALL_DIR" ]; then
        sudo rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}✓ Removed $INSTALL_DIR${NC}"
    fi
    
    echo -e "${GREEN}✓ epub2md uninstalled successfully!${NC}"
}

run_local() {
    # Run from local development environment
    if [ -d "$SCRIPT_DIR/.venv" ]; then
        "$SCRIPT_DIR/.venv/bin/python" -m epub2md "$@"
    elif [ -d "$SCRIPT_DIR/venv" ]; then
        "$SCRIPT_DIR/venv/bin/python" -m epub2md "$@"
    else
        python3 -m epub2md "$@"
    fi
}

# Main command handling
case "${1:-}" in
    install)
        do_install
        ;;
    uninstall)
        do_uninstall
        ;;
    check)
        check_prerequisites
        ;;
    help|--help|-h|"")
        show_help
        ;;
    convert|batch)
        # Pass through to Python module
        if [ -f "$INSTALL_DIR/.venv/bin/python" ]; then
            # Installed version
            exec "$INSTALL_DIR/.venv/bin/python" -m epub2md "$@"
        else
            # Local development version
            run_local "$@"
        fi
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
