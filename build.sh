#!/bin/bash
# Build script for OBS Snap Filter Plugin

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$SCRIPT_DIR/obs-snapfilter-plugin"
BUILD_DIR="$PLUGIN_DIR/build"
OBS_SOURCE_DIR="${OBS_SOURCE_DIR:-../obs-studio}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building OBS Snap Filter Plugin...${NC}"

# Check dependencies
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        exit 1
    fi
}

echo "Checking dependencies..."
check_dependency cmake
check_dependency g++

# Check for OpenCV
if ! pkg-config --exists opencv4 2>/dev/null && ! pkg-config --exists opencv 2>/dev/null; then
    echo -e "${RED}Error: OpenCV not found. Please install libopencv-dev${NC}"
    exit 1
fi

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure
echo "Configuring with CMake..."
cmake .. \
    -DOBS_SOURCE_DIR="$OBS_SOURCE_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TESTS=OFF

# Build
echo "Building..."
cmake --build . --config Release -j$(nproc)

echo -e "${GREEN}Build complete!${NC}"
echo ""
echo "To install, run:"
echo "  cd $BUILD_DIR && sudo cmake --install ."
echo ""
echo "Or manually copy:"
echo "  - obs-snapfilter.so -> /usr/lib/obs-plugins/"
echo "  - data/obs-plugins/obs-snapfilter/* -> /usr/share/obs/obs-plugins/obs-snapfilter/"
