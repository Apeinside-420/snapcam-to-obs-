# Windows Installation Guide for Snap Camera Filter

## Where to Save the Script on Windows

### OBS Scripts Folder Location:
```
%APPDATA%\obs-studio\scripts\
```

**Full path usually:**
- Windows 10/11: `C:\Users\[YourUsername]\AppData\Roaming\obs-studio\scripts\`

### Quick Steps:

1. **Press `Win + R`** (opens Run dialog)
2. **Type:** `%APPDATA%\obs-studio\scripts\`
3. **Press Enter**
4. Copy `snap_filter.py` to that folder

### Alternative Method:

1. Open File Explorer
2. Navigate to: `C:\Users\[YourUsername]\AppData\Roaming\obs-studio\`
3. Create folder `scripts` if it doesn't exist
4. Copy `snap_filter.py` into it

### Installing Dependencies on Windows:

Open **Command Prompt** or **PowerShell** as Administrator:

```cmd
pip install opencv-python Pillow numpy
```

Or if pip is not found:
```cmd
python -m pip install opencv-python Pillow numpy
```

### Then in OBS Studio:

1. Open OBS
2. Go to **Tools > Scripts**
3. Click the **+** button
4. Select `snap_filter.py` from the scripts folder
5. The filter will appear in your video source filters!

### Converting Lenses on Windows:

```cmd
python "C:\path\to\snap_lens_converter.py" "C:\path\to\your\lens.lns" -o "C:\converted-lenses\"
```

---

## Summary of Windows Paths:

| Component | Windows Path |
|-----------|--------------|
| **OBS Scripts** | `%APPDATA%\obs-studio\scripts\` |
| **Python** | Usually `C:\Users\[Username]\AppData\Local\Programs\Python\Python3xx` |
| **Lenses** | Your download location (e.g., `C:\Users\[Username]\Downloads\`) |

---

**Note:** The script is the same for all platforms - only the installation location differs!
