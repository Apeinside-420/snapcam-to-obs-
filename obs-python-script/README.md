# OBS Python Script Installation & Usage Guide

## Overview

This Python script provides a **no-compilation-required** alternative to the C++ plugin, using OBS Studio's built-in Python scripting support.

## Features

- ✅ **No compilation needed** - Pure Python solution
- ✅ Real-time face detection using OpenCV
- ✅ 6 different filter effects:
  - Beauty (Skin Smoothing)
  - Cartoon
  - Face Glow
  - Color Tint
  - Edge Detection
  - Blur
- ✅ Face-tracked region effects
- ✅ Adjustable parameters via OBS UI
- ✅ Load converted Snap Camera lenses
- ✅ Works on Windows, macOS, and Linux

## Prerequisites

### Required Software

1. **OBS Studio** 28.0 or newer with Python scripting enabled
2. **Python** 3.8 or newer
3. **OpenCV** Python bindings

### Installing Dependencies

#### Ubuntu/Debian
```bash
# Install system packages
sudo apt-get update
sudo apt-get install python3 python3-pip python3-opencv opencv-data

# Install Python packages
pip3 install -r requirements.txt
```

#### Windows
```powershell
# Install Python from python.org, then:
pip install opencv-python Pillow numpy
```

#### macOS
```bash
# Using Homebrew:
brew install python opencv
pip3 install Pillow numpy
```

## Installation

### Step 1: Copy Script to OBS

Copy `snap_filter.py` to your OBS scripts folder:

- **Linux**: `~/.config/obs-studio/scripts/`
- **Windows**: `%APPDATA%\obs-studio\scripts\`
- **macOS**: `~/Library/Application Support/obs-studio/scripts/`

```bash
# Linux example:
mkdir -p ~/.config/obs-studio/scripts/
cp obs-python-script/snap_filter.py ~/.config/obs-studio/scripts/
```

### Step 2: Configure OBS Python Settings

1. Open OBS Studio
2. Go to **Tools > Scripts**
3. Click the **Python Settings** tab
4. Set the Python install path (usually auto-detected)
5. Click **+** (Plus) button to add the script
6. Select `snap_filter.py`

### Step 3: Enable the Filter

1. Right-click any video source (camera, media, etc.)
2. Select **Filters**
3. Under **Effect Filters**, click **+**
4. Choose **Snap Camera Filter (Python)**
5. Configure settings in the filter properties

## Usage

### Basic Controls

- **Enable Face Tracking**: Toggle face detection on/off
- **Filter Intensity**: Adjust effect strength (0.0 - 1.0)
- **Effect Type**: Choose from 6 different effects
- **Tint Color**: Change color for tint effect
- **Tracking Smoothness**: Adjust face tracking smoothness (0.0 - 1.0)
- **Detection Confidence**: Minimum confidence for face detection

### Loading Converted Lenses

1. Convert your Snap Camera lens:
```bash
python3 lens-converter/snap_lens_converter.py /path/to/lens.lns -o converted/
```

2. In the filter properties, click **Lens File**
3. Select the converted `lens_info.json` file
4. The lens settings will be loaded automatically

## Filter Effects Explained

### Beauty (Skin Smoothing)
- Applies bilateral filtering to skin regions
- Subtle brightness increase
- Configurable intensity

### Cartoon
- Edge detection using adaptive thresholding
- Color quantization with k-means clustering
- Creates comic book aesthetic

### Face Glow
- Gaussian blur centered on detected face
- Adjustable glow radius via intensity
- Creates ethereal/fantasy effect

### Color Tint
- Applies color overlay to entire frame
- Use the **Tint Color** picker
- Adjustable opacity via intensity

### Edge Detection
- Canny edge detection
- Inverted edges for artistic look
- Blend with original frame

### Blur
- Gaussian blur with kernel size based on intensity
- Subtle to heavy blur options

## Troubleshooting

### "ModuleNotFoundError: No module named 'cv2'"

Install OpenCV:
```bash
pip3 install opencv-python
```

### Face tracking not working

1. Check that OpenCV data files are installed:
```bash
# Ubuntu/Debian
sudo apt-get install opencv-data

# Or manually download:
# https://github.com/opencv/opencv/tree/master/data/haarcascades
```

2. Ensure good lighting and face visibility
3. Adjust **Detection Confidence** threshold

### Script doesn't appear in OBS

1. Verify Python is installed: `python3 --version`
2. Check OBS Python settings: Tools > Scripts > Python Settings
3. Ensure script is in correct folder
4. Check OBS log for errors: Help > Log Files > View Current Log

### Performance issues

- Reduce filter intensity
- Disable face tracking if not needed
- Lower output resolution in OBS
- Close other resource-intensive applications

## Advanced Configuration

### Custom Effects

Edit the `SnapFilter` class in `snap_filter.py` to add custom effects:

```python
def apply_custom(self, frame):
    # Your custom OpenCV processing here
    return processed_frame
```

### Face Detection Models

The script uses Haar cascades by default. To use DNN models (more accurate but slower):

1. Download Caffe model files
2. Modify the `detect_faces()` function
3. Uncomment the DNN detection code (included as comments in script)

## Comparison: Python Script vs C++ Plugin

| Feature | Python Script | C++ Plugin |
|---------|---------------|------------|
| Installation | Easy (no compile) | Requires build tools |
| Performance | Good (CPU) | Excellent (GPU) |
| Face Tracking | Yes | Yes |
| Custom Shaders | Limited | Full HLSL support |
| 3D Overlays | No | Planned |
| Real-time | Yes | Yes |
| Cross-platform | Yes | Yes |

## Development

### Adding New Effects

1. Add to effect list in `script_properties()`:
```python
obs.obs_property_list_add_string(effect_list, "My Effect", "myeffect")
```

2. Add processing method:
```python
def apply_myeffect(self, frame):
    # Process frame
    return processed
```

3. Add case in `process_frame()`:
```python
elif self.effect_type == "myeffect":
    frame = self.apply_myeffect(frame)
```

### Debugging

Enable debug output by adding to `script_load()`:
```python
obs.obs_script_log(obs.LOG_INFO, "Debug message")
```

## License

GPL-2.0 - See LICENSE file

## Credits

- OBS Studio team for Python scripting API
- OpenCV team for computer vision library
- Snap Inc. for original lens concepts
