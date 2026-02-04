#!/bin/bash
# Quick install script for the OBS Snap Filter Plugin

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$SCRIPT_DIR/obs-snapfilter-plugin"
BUILD_DIR="$PLUGIN_DIR/build"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OBS_PLUGINS_DIR="/usr/lib/obs-plugins"
    OBS_DATA_DIR="/usr/share/obs/obs-plugins"
    echo "Detected Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OBS_PLUGINS_DIR="/Applications/OBS.app/Contents/PlugIns"
    OBS_DATA_DIR="/Applications/OBS.app/Contents/Resources/data/obs-plugins"
    echo "Detected macOS"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Installing OBS Snap Filter Plugin..."

# Check if built
if [ ! -f "$BUILD_DIR/obs-snapfilter.so" ] && [ ! -f "$BUILD_DIR/obs-snapfilter.dll" ]; then
    echo "Plugin not built yet. Run ./build.sh first."
    exit 1
fi

# Install plugin binary
echo "Installing plugin binary..."
if [ -f "$BUILD_DIR/obs-snapfilter.so" ]; then
    sudo cp "$BUILD_DIR/obs-snapfilter.so" "$OBS_PLUGINS_DIR/"
    sudo chmod 755 "$OBS_PLUGINS_DIR/obs-snapfilter.so"
elif [ -f "$BUILD_DIR/obs-snapfilter.dll" ]; then
    sudo cp "$BUILD_DIR/obs-snapfilter.dll" "$OBS_PLUGINS_DIR/"
fi

# Install data files
echo "Installing data files..."
sudo mkdir -p "$OBS_DATA_DIR/obs-snapfilter"
sudo cp -r "$PLUGIN_DIR/data/"* "$OBS_DATA_DIR/obs-snapfilter/"

# Install lens converter
echo "Installing lens converter..."
sudo cp "$SCRIPT_DIR/lens-converter/snap_lens_converter.py" /usr/local/bin/snap-lens-convert
sudo chmod +x /usr/local/bin/snap-lens-convert

echo "Installation complete!"
echo ""
echo "Usage:"
echo "  1. Restart OBS Studio"
echo "  2. Add 'Snap Camera Filter' to any video source"
echo "  3. Convert lenses: snap-lens-convert /path/to/lens.lns"
