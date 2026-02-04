#!/bin/bash
# Quick test of the Snap Camera to OBS system

echo "Snap Camera to OBS - Quick Test"
echo "================================"
echo ""

# Check Python packages
echo "✓ Checking Python packages..."
python3 -c "import cv2, numpy, PIL; print('  - OpenCV:', cv2.__version__)"

# Check OBS script
echo "✓ Checking OBS script..."
if [ -f ~/.config/obs-studio/scripts/snap_filter.py ]; then
    echo "  - Script installed: ~/.config/obs-studio/scripts/snap_filter.py"
else
    echo "  ✗ Script not found!"
fi

# Check lens converter
echo "✓ Checking lens converter..."
if [ -f ~/projects/snapcam-to-obs/lens-converter/snap_lens_converter.py ]; then
    echo "  - Converter ready: ~/projects/snapcam-to-obs/lens-converter/snap_lens_converter.py"
else
    echo "  - Converter ready: /home/apein/projects/snapcam-to-obs/lens-converter/snap_lens_converter.py"
fi

echo ""
echo "Next steps:"
echo "1. Open OBS Studio"
echo "2. Go to Tools > Scripts"
echo "3. Click '+' and select: ~/.config/obs-studio/scripts/snap_filter.py"
echo "4. Add filter to any video source:"
echo "   - Right-click source > Filters > '+' > 'Snap Camera Filter (Python)'"
echo ""
echo "To convert a lens:"
echo "  python3 ~/projects/snapcam-to-obs/lens-converter/snap_lens_converter.py /path/to/lens.lns -o ~/converted-lenses/"
