# Build Instructions - OBS Snap Filter Plugin

## Prerequisites

### Required Packages
```bash
sudo apt-get update
sudo apt-get install -y \
    cmake \
    build-essential \
    pkg-config \
    libopencv-dev \
    obs-studio \
    obs-studio-dev
```

### Package Versions
- CMake 3.16 or higher
- OpenCV 4.x
- OBS Studio 28+
- C++17 compatible compiler (GCC 7+, Clang 5+)

## Build Steps

### Option 1: Using build.sh (Recommended)

```bash
cd /home/apein/projects/snapcam-to-obs
./build.sh
```

This script will:
1. Check for required dependencies
2. Create build directory
3. Run CMake configuration
4. Build the plugin in Release mode

### Option 2: Manual Build

```bash
cd /home/apein/projects/snapcam-to-obs/obs-snapfilter-plugin
mkdir -p build
cd build

# Configure
cmake .. \
    -DOBS_SOURCE_DIR=/usr/include/obs \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TESTS=OFF

# Build
cmake --build . --config Release -j$(nproc)
```

### Option 3: With OBS Source Build

If you built OBS from source:

```bash
cd obs-snapfilter-plugin/build
cmake .. \
    -DOBS_SOURCE_DIR=/path/to/obs-studio \
    -DCMAKE_BUILD_TYPE=Release

cmake --build . --config Release
```

## Installation

### System-wide Installation (Requires sudo)

```bash
cd obs-snapfilter-plugin/build
sudo cmake --install .
```

This installs:
- Plugin library → `/usr/lib/obs-plugins/obs-snapfilter.so`
- Data files → `/usr/share/obs/obs-plugins/obs-snapfilter/`

### User Installation (No sudo required)

```bash
# Plugin
mkdir -p ~/.config/obs-studio/plugins/obs-snapfilter/bin/64bit
cp obs-snapfilter-plugin/build/obs-snapfilter.so \
   ~/.config/obs-studio/plugins/obs-snapfilter/bin/64bit/

# Data files
mkdir -p ~/.config/obs-studio/plugins/obs-snapfilter/data
cp -r obs-snapfilter-plugin/data/* \
   ~/.config/obs-studio/plugins/obs-snapfilter/data/
```

## Verification

After installation, verify the plugin loads:

```bash
# Check if plugin file exists
ls -lh ~/.config/obs-studio/plugins/obs-snapfilter/bin/64bit/obs-snapfilter.so
# or
ls -lh /usr/lib/obs-plugins/obs-snapfilter.so

# Start OBS and check logs
obs --verbose 2>&1 | grep -i "snap"
```

In OBS Studio:
1. Add a video source
2. Right-click → Filters
3. Click + under Effect Filters
4. Look for "Snap Camera Filter"

## Troubleshooting

### CMake can't find OBS headers

```bash
# Install OBS development headers
sudo apt-get install obs-studio-dev

# Or specify OBS source directory
cmake .. -DOBS_SOURCE_DIR=/path/to/obs-studio
```

### OpenCV not found

```bash
# Check OpenCV installation
pkg-config --modversion opencv4

# If not installed
sudo apt-get install libopencv-dev
```

### Build errors with libobs

Make sure you have the OBS development headers:

```bash
dpkg -l | grep obs-studio
# Should show both obs-studio and obs-studio-dev
```

### Plugin doesn't appear in OBS

1. Check OBS log file: `~/.config/obs-studio/logs/`
2. Look for loading errors
3. Verify file permissions (should be readable)
4. Check architecture (must be 64-bit on 64-bit system)

## Build Configuration Options

### Debug Build

```bash
cmake .. -DCMAKE_BUILD_TYPE=Debug
```

### With Tests

```bash
cmake .. -DBUILD_TESTS=ON
make test
```

### With MediaPipe (Optional)

For advanced face tracking with MediaPipe:

```bash
cmake .. -DMEDIAPIPE_DIR=/path/to/mediapipe
```

## Clean Build

```bash
cd obs-snapfilter-plugin
rm -rf build
mkdir build
cd build
cmake .. && make
```

## Build Output

After successful build, you should see:
- `obs-snapfilter-plugin/build/obs-snapfilter.so` - Main plugin library
- Data files copied to install directory

## Next Steps

After building:
1. Install the plugin (see Installation section)
2. Restart OBS Studio
3. Test with Python script first (simpler debugging)
4. Add C++ plugin filter to a video source
5. Check performance and adjust settings
