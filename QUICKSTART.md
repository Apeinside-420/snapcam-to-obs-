# Quick Start Guide - Snap Camera to OBS

## ✅ What Was Built For You

Two complete solutions were created:

### Solution 1: Python OBS Script (RECOMMENDED - No Build Required)
- **File**: `obs-python-script/snap_filter.py` (573 lines)
- **Features**: Face tracking + 6 filter effects
- **Requirements**: Just Python + OpenCV (installs in 2 minutes)
- **Works on**: Windows, macOS, Linux

### Solution 2: C++ OBS Plugin (Full Performance)
- **Files**: `obs-snapfilter-plugin/` (19 files, ~2000 lines)
- **Features**: GPU shaders, maximum performance
- **Requirements**: CMake, OpenCV-dev, OBS Studio headers
- **Works on**: All platforms (requires compilation)

### Solution 3: Lens Converter
- **File**: `lens-converter/snap_lens_converter.py` (290 lines)
- **Purpose**: Extract and convert `.lns` files from Snap Camera
- **Works with**: Both solutions above

---

## 🚀 QUICK START (5 Minutes)

### Step 1: Install Python Version (Easiest)

**On Ubuntu/Debian:**
```bash
cd /home/apein/projects/snapcam-to-obs
./setup-python.sh
```

**Or manually:**
```bash
# Install dependencies
pip3 install opencv-python Pillow numpy

# Copy script to OBS
mkdir -p ~/.config/obs-studio/scripts/
cp obs-python-script/snap_filter.py ~/.config/obs-studio/scripts/

# Install lens converter
cp lens-converter/snap_lens_converter.py ~/.local/bin/snap-lens-convert
chmod +x ~/.local/bin/snap-lens-convert
```

### Step 2: Enable in OBS

1. Open OBS Studio
2. Go to **Tools > Scripts**
3. Click **+** button (bottom left)
4. Select `snap_filter.py`
5. Configure settings

### Step 3: Use the Filter

1. Right-click any video source → **Filters**
2. Click **+** under Effect Filters
3. Select **"Snap Camera Filter (Python)"**
4. Adjust settings:
   - Enable Face Tracking: ✓
   - Effect Type: Beauty / Cartoon / Glow / etc.
   - Filter Intensity: 0.0 - 1.0

---

## 📦 Converting Snap Camera Lenses

### Convert a Single Lens:
```bash
# Convert a .lns file
snap-lens-convert /path/to/your/lens.lns -o ~/converted-lenses/

# Or use Python directly
python3 lens-converter/snap_lens_converter.py ~/Downloads/my-filter.lns -o ~/converted-lenses/
```

### Batch Convert All Lenses:
```bash
python3 lens-converter/snap_lens_converter.py ~/Snap\ Camera/Lenses/ --batch -o ~/converted-lenses/
```

### Using Converted Lenses:
1. Convert the lens (above)
2. In OBS filter properties, click **Lens File**
3. Select the `lens_info.json` from converted folder
4. The filter settings will load automatically

---

## 🔧 Building C++ Plugin (For Advanced Users)

If you want the compiled C++ version for maximum performance:

### Prerequisites:
```bash
sudo apt-get update
sudo apt-get install -y cmake pkg-config libopencv-dev \
    libjsoncpp-dev build-essential obs-studio-dev
```

### Build:
```bash
cd /home/apein/projects/snapcam-to-obs
./build.sh
```

### Install:
```bash
sudo ./install.sh
```

---

## 📁 Project Structure

```
snapcam-to-obs/
├── README.md                          # Main documentation
├── build.sh                           # Build C++ plugin
├── install.sh                         # Install C++ plugin
├── setup-python.sh                    # Setup Python script
│
├── lens-converter/
│   └── snap_lens_converter.py         # Lens extraction tool
│
├── obs-python-script/                 # PYTHON SOLUTION ⭐
│   ├── snap_filter.py                 # Main OBS script
│   ├── requirements.txt               # Python dependencies
│   └── README.md                      # Python script docs
│
└── obs-snapfilter-plugin/             # C++ SOLUTION
    ├── CMakeLists.txt                 # Build configuration
    ├── src/                           # C++ source files
    ├── include/                       # Headers
    └── data/                          # Shaders & resources
```

---

## 🎯 Features Available

### Face Tracking (Both Solutions)
✅ Real-time face detection using OpenCV  
✅ Smooth tracking with configurable interpolation  
✅ Face position, size, and rotation detection  
✅ Multi-face support (uses largest face)  
✅ Eye detection for rotation estimation  

### Filter Effects (Python Script)
1. **Beauty** - Skin smoothing, whitening, brightness
2. **Cartoon** - Edge detection + color quantization
3. **Face Glow** - Gaussian blur centered on face
4. **Color Tint** - Adjustable color overlay
5. **Edge Detection** - Canny edge detection
6. **Blur** - Configurable Gaussian blur

### Filter Effects (C++ Plugin)
All Python effects PLUS:
- GPU-accelerated HLSL shaders
- Custom shader support
- 3D overlay support (planned)
- Maximum performance

---

## 🐛 Troubleshooting

### "No module named 'cv2'"
```bash
pip3 install opencv-python
```

### Face tracking not working
1. Check OpenCV data files:
```bash
ls /usr/share/opencv*/haarcascades/haarcascade_frontalface_default.xml
# If not found:
sudo apt-get install opencv-data
```

2. Ensure good lighting and face visibility

### Script doesn't appear in OBS
1. Check Python path: `Tools > Scripts > Python Settings`
2. Verify script is in correct folder
3. Check OBS log: `Help > Log Files > View Current Log`

### Performance issues
- Reduce filter intensity
- Lower output resolution in OBS
- Disable face tracking if not needed

---

## 📖 Documentation

- **Main README**: `/home/apein/projects/snapcam-to-obs/README.md`
- **Python Script Guide**: `/home/apein/projects/snapcam-to-obs/obs-python-script/README.md`
- **C++ Plugin Structure**: `/home/apein/projects/snapcam-to-obs/obs-snapfilter-plugin/PROJECT_STRUCTURE.txt`

---

## 🎉 You're Ready!

1. ✅ Lens converter created (290 lines)
2. ✅ Python OBS script created (573 lines, 6 effects)
3. ✅ C++ plugin created (2000+ lines, full GPU shaders)
4. ✅ All documentation written
5. ✅ Installation scripts ready

**Next step**: Run `./setup-python.sh` to get started in 2 minutes!

---

## 💡 Pro Tips

- **Start with Python script** - it's ready to use immediately
- **Convert your favorite lenses** before Snap Camera shuts down
- **Combine effects** - use multiple filter instances
- **Adjust tracking smoothness** for best results (0.3 is good default)
- **Use with any video source** - cameras, screen capture, media files

Enjoy your Snap Camera filters in OBS! 🎬✨
