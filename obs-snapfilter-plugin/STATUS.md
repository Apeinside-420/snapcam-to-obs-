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

4. **macOS Compatibility**
   - Fixed OpenCV/ObjC `NO` macro conflict by using specific headers
   - Moved `OBS_DECLARE_MODULE()` from header to source file
   - Added simde dependency for SIMD support
   - Added support for OBS source directory build path

### Files Modified

- `src/snap-filter.h` - Data type definitions, OpenCV include fix
- `src/snap-filter.cpp` - All API calls and rendering
- `src/face-tracker.h` - OpenCV include fix, forward declarations
- `src/face-tracker.cpp` - Fixed typedef usage
- `src/main.cpp` - OBS module macros
- `include/obs-snapfilter.h` - Removed duplicate module macros
- `CMakeLists.txt` - Version requirements, macOS build support

### Building

**Prerequisites:**

```bash
# macOS
brew install cmake opencv jsoncpp simde
brew install --cask obs

# Clone OBS source for headers (macOS doesn't have libobs-dev)
git clone --depth 1 --branch 32.0.4 https://github.com/obsproject/obs-studio.git /tmp/obs-sdk/obs-studio

# Linux (Ubuntu/Debian)
sudo apt install cmake libobs-dev libopencv-dev libjsoncpp-dev

# Windows (using vcpkg)
vcpkg install opencv4:x64-windows jsoncpp:x64-windows
# Download OBS source or SDK from https://github.com/obsproject/obs-studio/releases
```

**Build:**

```bash
cd obs-snapfilter-plugin
mkdir build && cd build

# macOS (requires OBS source path)
cmake .. -DOBS_SOURCE_DIR=/tmp/obs-sdk/obs-studio
make

# Linux (with pkg-config)
cmake ..
make

# Windows (Visual Studio)
cmake .. -G "Visual Studio 17 2022" -A x64 ^
    -DOBS_SOURCE_DIR=C:/path/to/obs-studio ^
    -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
cmake --build . --config Release
```

**Install:**

Copy the built plugin to your OBS plugins folder:

**Linux:**
```bash
mkdir -p ~/.config/obs-studio/plugins/obs-snapfilter/bin/64bit
cp obs-snapfilter.so ~/.config/obs-studio/plugins/obs-snapfilter/bin/64bit/
```

**macOS:**
```bash
mkdir -p ~/Library/Application\ Support/obs-studio/plugins/obs-snapfilter.plugin/Contents/MacOS
cp obs-snapfilter.so ~/Library/Application\ Support/obs-studio/plugins/obs-snapfilter.plugin/Contents/MacOS/obs-snapfilter
```

**Windows:**
```cmd
mkdir "%APPDATA%\obs-studio\plugins\obs-snapfilter\bin\64bit"
copy obs-snapfilter.dll "%APPDATA%\obs-studio\plugins\obs-snapfilter\bin\64bit\"
```

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
