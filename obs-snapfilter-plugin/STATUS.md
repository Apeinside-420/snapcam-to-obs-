# C++ Plugin Status

## Current Status: OBS 30+ Compatible ✅

The C++ OBS plugin has been updated to work with **OBS Studio 30.x and later**.

### What Was Fixed

The original codebase had several API compatibility issues with OBS 30+:

1. **Data Types Updated**
   - Changed `float[2]` arrays to `struct vec2` for face tracking data
   - Changed `float[4]` arrays to `struct vec4` for color data
   - Added required includes: `<graphics/vec2.h>`, `<graphics/vec4.h>`

2. **API Function Calls Fixed**
   - `gs_effect_set_vec2()` and `gs_effect_set_vec4()` now receive proper `struct vec2*` and `struct vec4*` pointers
   - Replaced broken `gs_texture_render_start/end` calls with correct `obs_source_process_filter_begin/end` pattern
   - Fixed memory leak from per-frame texture creation

3. **Build System Updated**
   - CMakeLists.txt now requires OBS 30.0.0 minimum
   - Added version check to fail fast if older OBS is detected

### Files Modified

- `src/snap-filter.h` - Data type definitions
- `src/snap-filter.cpp` - All API calls and rendering
- `CMakeLists.txt` - Version requirements

### Building

**Prerequisites:**

```bash
# macOS
brew install cmake opencv jsoncpp
# OBS SDK: Download from https://github.com/obsproject/obs-studio/releases

# Linux (Ubuntu/Debian)
sudo apt install cmake libobs-dev libopencv-dev libjsoncpp-dev

# Windows
# Install CMake, OpenCV, jsoncpp, and OBS SDK
```

**Build:**

```bash
cd obs-snapfilter-plugin
mkdir build && cd build
cmake ..
make
```

**Install:**

Copy the built `obs-snapfilter.so` (Linux/macOS) or `obs-snapfilter.dll` (Windows) to your OBS plugins folder:
- Linux: `~/.config/obs-studio/plugins/`
- macOS: `~/Library/Application Support/obs-studio/plugins/`
- Windows: `%APPDATA%\obs-studio\plugins\`

### Features

- ✅ Real-time face tracking with OpenCV
- ✅ Custom shader effects with face data
- ✅ Configurable filter intensity and tint color
- ✅ Smooth tracking interpolation
- ✅ Background thread for face detection

### Alternative: Python Script

If you prefer a no-compile solution, use the Python script instead:

```bash
# Copy to OBS scripts folder
cp obs-python-script/snap_filter.py ~/.config/obs-studio/scripts/

# In OBS: Tools → Scripts → Add → snap_filter.py
```

See `obs-python-script/README.md` for details.

---

**Last Updated:** February 3, 2026
