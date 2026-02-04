#!/bin/bash
# Quick setup script for the Python OBS Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Setting up Snap Camera Filter (Python version)...${NC}"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OBS_SCRIPTS_DIR="$HOME/.config/obs-studio/scripts"
    echo -e "${GREEN}Detected Linux${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OBS_SCRIPTS_DIR="$HOME/Library/Application Support/obs-studio/scripts"
    echo -e "${GREEN}Detected macOS${NC}"
else
    # Windows with Git Bash or similar
    OBS_SCRIPTS_DIR="$APPDATA/obs-studio/scripts"
    echo -e "${GREEN}Detected Windows${NC}"
fi

# Check Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or newer"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Found Python: $PYTHON_VERSION${NC}"

# Check pip
echo "Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Error: pip3 is not installed${NC}"
    echo "Please install pip"
    exit 1
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/obs-python-script/requirements.txt" --user

# Create OBS scripts directory
echo ""
echo "Creating OBS scripts directory..."
mkdir -p "$OBS_SCRIPTS_DIR"

# Copy script
echo "Installing Python script to OBS..."
cp "$SCRIPT_DIR/obs-python-script/snap_filter.py" "$OBS_SCRIPTS_DIR/"

# Copy lens converter
echo "Installing lens converter..."
mkdir -p "$HOME/.local/bin"
cp "$SCRIPT_DIR/lens-converter/snap_lens_converter.py" "$HOME/.local/bin/snap-lens-convert"
chmod +x "$HOME/.local/bin/snap-lens-convert"

# Check if local bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo -e "${YELLOW}Note: ~/.local/bin is not in your PATH${NC}"
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo 'export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Open OBS Studio"
echo "2. Go to Tools > Scripts"
echo "3. Click Python Settings tab and verify Python path"
echo "4. Click the + button and select 'snap_filter.py'"
echo "5. Add 'Snap Camera Filter (Python)' to any video source"
echo ""
echo "To convert lenses:"
echo "  snap-lens-convert /path/to/lens.lns -o output/"
echo ""
echo "Script location: $OBS_SCRIPTS_DIR/snap_filter.py"
