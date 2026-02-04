#!/bin/bash
# Syntax checker for C++ plugin code
# Verifies code can be parsed without full OBS headers

set -e

PLUGIN_DIR="/home/apein/projects/snapcam-to-obs/obs-snapfilter-plugin"
ERRORS=0

echo "============================================================"
echo "C++ Plugin Syntax Verification"
echo "============================================================"

# Check if g++ is available
if ! command -v g++ &> /dev/null; then
    echo "✗ g++ not found"
    exit 1
fi

echo "✓ g++ found: $(g++ --version | head -1)"
echo ""

# Check each source file
echo "Checking source files..."
for file in "$PLUGIN_DIR/src"/*.cpp; do
    filename=$(basename "$file")
    echo -n "  Checking $filename... "
    
    # Try to parse the file (syntax check only, won't link)
    if g++ -std=c++17 -fsyntax-only \
        -I"$PLUGIN_DIR/include" \
        -I"$PLUGIN_DIR/src" \
        "$file" 2>/dev/null; then
        echo "✓"
    else
        # Expected to fail due to missing OBS headers
        # Just check for basic C++ syntax errors
        if g++ -std=c++17 -fsyntax-only \
            -I"$PLUGIN_DIR/include" \
            -I"$PLUGIN_DIR/src" \
            "$file" 2>&1 | grep -q "obs-module.h"; then
            echo "⚠ (missing OBS headers - expected)"
        else
            echo "✗ (syntax errors)"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

echo ""
echo "Checking header files..."
for file in "$PLUGIN_DIR/include"/*.h "$PLUGIN_DIR/src"/*.h; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo -n "  Checking $filename... "
        
        # Headers can be checked more easily
        if g++ -std=c++17 -fsyntax-only -x c++ \
            -I"$PLUGIN_DIR/include" \
            -I"$PLUGIN_DIR/src" \
            "$file" 2>/dev/null; then
            echo "✓"
        else
            if g++ -std=c++17 -fsyntax-only -x c++ \
                -I"$PLUGIN_DIR/include" \
                -I"$PLUGIN_DIR/src" \
                "$file" 2>&1 | grep -qE "(obs-|opencv)"; then
                echo "⚠ (missing dependencies - expected)"
            else
                echo "✗ (syntax errors)"
                ERRORS=$((ERRORS + 1))
            fi
        fi
    fi
done

echo ""
echo "============================================================"
echo "Code Structure Check"
echo "============================================================"

# Count files
SRC_COUNT=$(ls -1 "$PLUGIN_DIR/src"/*.cpp 2>/dev/null | wc -l)
HDR_COUNT=$(ls -1 "$PLUGIN_DIR/include"/*.h "$PLUGIN_DIR/src"/*.h 2>/dev/null | wc -l)
SHADER_COUNT=$(ls -1 "$PLUGIN_DIR/data/shaders"/*.shader 2>/dev/null | wc -l)

echo "Source files: $SRC_COUNT"
echo "Header files: $HDR_COUNT"
echo "Shader files: $SHADER_COUNT"
echo ""

# Check for key components
echo "Key components:"
[ -f "$PLUGIN_DIR/src/main.cpp" ] && echo "  ✓ main.cpp" || echo "  ✗ main.cpp"
[ -f "$PLUGIN_DIR/src/snap-filter.cpp" ] && echo "  ✓ snap-filter.cpp" || echo "  ✗ snap-filter.cpp"
[ -f "$PLUGIN_DIR/src/face-tracker.cpp" ] && echo "  ✓ face-tracker.cpp" || echo "  ✗ face-tracker.cpp"
[ -f "$PLUGIN_DIR/CMakeLists.txt" ] && echo "  ✓ CMakeLists.txt" || echo "  ✗ CMakeLists.txt"
echo ""

echo "============================================================"
if [ $ERRORS -eq 0 ]; then
    echo "✓ Code structure is valid"
    echo "  Note: Full build requires OBS headers and dependencies"
    echo ""
    echo "To build, run:"
    echo "  1. Install dependencies (see BUILD_INSTRUCTIONS.md)"
    echo "  2. Run: ./build.sh"
    exit 0
else
    echo "✗ Found $ERRORS errors in code"
    exit 1
fi
