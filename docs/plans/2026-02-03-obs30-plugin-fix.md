# OBS 30+ C++ Plugin Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the obs-snapfilter C++ plugin to compile and work with OBS Studio 30+

**Architecture:** The plugin uses the standard OBS filter pattern (`obs_source_process_filter_begin/end`) with custom shader effects. Face tracking runs in a background thread using OpenCV Haar cascades. The main fixes involve updating data types from `float[]` arrays to proper OBS `struct vec2/vec4` types, and replacing the broken render function with the correct OBS filter rendering pattern.

**Tech Stack:** C++17, OBS Studio 30+ API, OpenCV 4.x, CMake 3.16+

---

## Summary of Issues

1. **Wrong parameter types**: Code uses `float[2]` and `float[4]` arrays, but OBS expects `struct vec2*` and `struct vec4*`
2. **Non-existent render functions**: `gs_texture_render_start/end` don't exist - must use `obs_source_process_filter_begin/end`
3. **Memory leak in render**: Creates/destroys texture every frame instead of reusing
4. **Missing includes**: Need `<graphics/vec2.h>` and `<graphics/vec4.h>` for OBS struct types

---

## Task 1: Fix Data Types in Header

**Files:**
- Modify: `obs-snapfilter-plugin/src/snap-filter.h:39-46`

**Step 1: Add required includes**

At the top of `snap-filter.h`, after the existing includes, add:

```cpp
#include <graphics/vec2.h>
#include <graphics/vec4.h>
```

**Step 2: Replace float arrays with OBS structs**

Change lines 39-46 from:

```cpp
// Face tracking data
float face_center[2];
float face_size[2];
float face_rotation;
float face_confidence;

// Filter parameters
float intensity;
float tint_color[4];
```

To:

```cpp
// Face tracking data (OBS 30+ uses struct vec2/vec4)
struct vec2 face_center;
struct vec2 face_size;
float face_rotation;
float face_confidence;

// Filter parameters
float intensity;
struct vec4 tint_color;
```

**Step 3: Verify header compiles**

Run:
```bash
cd obs-snapfilter-plugin && mkdir -p build && cd build && cmake .. 2>&1 | head -50
```

Expected: CMake configures without errors (may have missing dependencies, that's ok)

**Step 4: Commit**

```bash
git add obs-snapfilter-plugin/src/snap-filter.h
git commit -m "fix(plugin): use OBS 30+ struct vec2/vec4 types in header"
```

---

## Task 2: Fix Data Initialization in Create Function

**Files:**
- Modify: `obs-snapfilter-plugin/src/snap-filter.cpp:40-52`

**Step 1: Update face_center/face_size initialization**

Change lines 40-46 from:

```cpp
// Initialize face data
filter->face_center[0] = 0.5f;
filter->face_center[1] = 0.5f;
filter->face_size[0] = 0.0f;
filter->face_size[1] = 0.0f;
filter->face_rotation = 0.0f;
filter->face_confidence = 0.0f;
```

To:

```cpp
// Initialize face data (use vec2_set for OBS 30+ structs)
vec2_set(&filter->face_center, 0.5f, 0.5f);
vec2_set(&filter->face_size, 0.0f, 0.0f);
filter->face_rotation = 0.0f;
filter->face_confidence = 0.0f;
```

**Step 2: Update tint_color initialization**

Change lines 48-52 from:

```cpp
// Initialize tint color
filter->tint_color[0] = 1.0f;
filter->tint_color[1] = 1.0f;
filter->tint_color[2] = 1.0f;
filter->tint_color[3] = 1.0f;
```

To:

```cpp
// Initialize tint color (use vec4_set for OBS 30+ structs)
vec4_set(&filter->tint_color, 1.0f, 1.0f, 1.0f, 1.0f);
```

**Step 3: Commit**

```bash
git add obs-snapfilter-plugin/src/snap-filter.cpp
git commit -m "fix(plugin): use vec2_set/vec4_set for data initialization"
```

---

## Task 3: Fix Color Loading in Update Function

**Files:**
- Modify: `obs-snapfilter-plugin/src/snap-filter.cpp:100-106`

**Step 1: Update color loading code**

Change lines 100-106 from:

```cpp
// Load color
uint32_t color = obs_data_get_int(settings, "tint_color");
filter->tint_color[0] = ((color >> 16) & 0xFF) / 255.0f;
filter->tint_color[1] = ((color >> 8) & 0xFF) / 255.0f;
filter->tint_color[2] = (color & 0xFF) / 255.0f;
filter->tint_color[3] = ((color >> 24) & 0xFF) / 255.0f;
```

To:

```cpp
// Load color (extract ARGB components into vec4)
uint32_t color = obs_data_get_int(settings, "tint_color");
vec4_set(&filter->tint_color,
    ((color >> 16) & 0xFF) / 255.0f,  // R
    ((color >> 8) & 0xFF) / 255.0f,   // G
    (color & 0xFF) / 255.0f,          // B
    ((color >> 24) & 0xFF) / 255.0f); // A
```

**Step 2: Commit**

```bash
git add obs-snapfilter-plugin/src/snap-filter.cpp
git commit -m "fix(plugin): use vec4_set for color loading"
```

---

## Task 4: Fix Face Tracking Data Update

**Files:**
- Modify: `obs-snapfilter-plugin/src/snap-filter.cpp:250-258`

**Step 1: Update smoothing code for vec2 structs**

Change lines 250-258 from:

```cpp
// Smooth the face data
float alpha = filter->smooth_factor;
filter->face_center[0] = filter->face_center[0] * (1.0f - alpha) + face_data.center_x * alpha;
filter->face_center[1] = filter->face_center[1] * (1.0f - alpha) + face_data.center_y * alpha;
filter->face_size[0] = filter->face_size[0] * (1.0f - alpha) + face_data.width * alpha;
filter->face_size[1] = filter->face_size[1] * (1.0f - alpha) + face_data.height * alpha;
filter->face_rotation = filter->face_rotation * (1.0f - alpha) + face_data.rotation * alpha;
filter->face_confidence = face_data.confidence;
filter->face_detected = face_data.confidence > 0.5f;
```

To:

```cpp
// Smooth the face data (accessing struct vec2 members with .x and .y)
float alpha = filter->smooth_factor;
filter->face_center.x = filter->face_center.x * (1.0f - alpha) + face_data.center_x * alpha;
filter->face_center.y = filter->face_center.y * (1.0f - alpha) + face_data.center_y * alpha;
filter->face_size.x = filter->face_size.x * (1.0f - alpha) + face_data.width * alpha;
filter->face_size.y = filter->face_size.y * (1.0f - alpha) + face_data.height * alpha;
filter->face_rotation = filter->face_rotation * (1.0f - alpha) + face_data.rotation * alpha;
filter->face_confidence = face_data.confidence;
filter->face_detected = face_data.confidence > 0.5f;
```

**Step 2: Commit**

```bash
git add obs-snapfilter-plugin/src/snap-filter.cpp
git commit -m "fix(plugin): access vec2 members correctly in smoothing code"
```

---

## Task 5: Fix Shader Parameter Setting

**Files:**
- Modify: `obs-snapfilter-plugin/src/snap-filter.cpp:285-305`

**Step 1: Update gs_effect_set_vec* calls to pass pointers**

Change lines 285-305 from:

```cpp
if (filter->param_face_center) {
    gs_effect_set_vec2(filter->param_face_center, filter->face_center);
}
if (filter->param_face_size) {
    gs_effect_set_vec2(filter->param_face_size, filter->face_size);
}
// ... etc
if (filter->param_tint_color) {
    gs_effect_set_vec4(filter->param_tint_color, filter->tint_color);
}
```

To:

```cpp
if (filter->param_face_center) {
    gs_effect_set_vec2(filter->param_face_center, &filter->face_center);
}
if (filter->param_face_size) {
    gs_effect_set_vec2(filter->param_face_size, &filter->face_size);
}
if (filter->param_face_rotation) {
    gs_effect_set_float(filter->param_face_rotation, filter->face_rotation);
}
if (filter->param_face_detected) {
    gs_effect_set_bool(filter->param_face_detected, filter->face_detected);
}
if (filter->param_elapsed_time) {
    gs_effect_set_float(filter->param_elapsed_time, filter->elapsed_time);
}
if (filter->param_intensity) {
    gs_effect_set_float(filter->param_intensity, filter->intensity);
}
if (filter->param_tint_color) {
    gs_effect_set_vec4(filter->param_tint_color, &filter->tint_color);
}
```

Note: The key change is adding `&` before struct variables to pass pointers.

**Step 2: Commit**

```bash
git add obs-snapfilter-plugin/src/snap-filter.cpp
git commit -m "fix(plugin): pass pointers to gs_effect_set_vec* functions"
```

---

## Task 6: Rewrite render_filter Function

**Files:**
- Modify: `obs-snapfilter-plugin/src/snap-filter.cpp:261-314`

This is the most critical fix. The current implementation uses non-existent functions and leaks memory.

**Step 1: Replace the entire render_filter function**

Delete lines 261-314 and replace with:

```cpp
void render_filter(snapfilter_data *filter, obs_source_t *target)
{
    // Use standard OBS filter rendering pattern
    if (!obs_source_process_filter_begin(filter->context, GS_RGBA,
                                          OBS_ALLOW_DIRECT_RENDERING))
        return;

    // Set shader parameters (within graphics context from process_filter_begin)
    {
        std::lock_guard<std::mutex> lock(filter->data_mutex);

        if (filter->param_face_center) {
            gs_effect_set_vec2(filter->param_face_center, &filter->face_center);
        }
        if (filter->param_face_size) {
            gs_effect_set_vec2(filter->param_face_size, &filter->face_size);
        }
        if (filter->param_face_rotation) {
            gs_effect_set_float(filter->param_face_rotation, filter->face_rotation);
        }
        if (filter->param_face_detected) {
            gs_effect_set_bool(filter->param_face_detected, filter->face_detected);
        }
        if (filter->param_elapsed_time) {
            gs_effect_set_float(filter->param_elapsed_time, filter->elapsed_time);
        }
        if (filter->param_intensity) {
            gs_effect_set_float(filter->param_intensity, filter->intensity);
        }
        if (filter->param_tint_color) {
            gs_effect_set_vec4(filter->param_tint_color, &filter->tint_color);
        }
    }

    // Render with custom effect
    obs_source_process_filter_end(filter->context, filter->effect, 0, 0);
}
```

**Step 2: Verify it compiles**

Run:
```bash
cd obs-snapfilter-plugin/build && make 2>&1 | head -100
```

Expected: May have linker errors for missing OBS libs, but no more type errors

**Step 3: Commit**

```bash
git add obs-snapfilter-plugin/src/snap-filter.cpp
git commit -m "fix(plugin): rewrite render_filter using OBS filter pattern"
```

---

## Task 7: Add OBS_ALLOW_DIRECT_RENDERING Include

**Files:**
- Modify: `obs-snapfilter-plugin/src/snap-filter.cpp:1-5`

**Step 1: Ensure obs-module.h is included for OBS_ALLOW_DIRECT_RENDERING**

The top of snap-filter.cpp should have:

```cpp
#include "snap-filter.h"
#include "shader-utils.h"
#include <obs-module.h>
#include <graphics/graphics.h>
#include <graphics/matrix4.h>
#include <graphics/vec2.h>
#include <graphics/vec4.h>
```

Add any missing includes.

**Step 2: Commit**

```bash
git add obs-snapfilter-plugin/src/snap-filter.cpp
git commit -m "fix(plugin): add required graphics includes"
```

---

## Task 8: Update CMakeLists.txt for OBS 30+

**Files:**
- Modify: `obs-snapfilter-plugin/CMakeLists.txt`

**Step 1: Add minimum OBS version requirement**

After line 3 (`set(CMAKE_CXX_STANDARD 17)`), add:

```cmake
# Require OBS 30+ for updated graphics API
set(OBS_MIN_VERSION "30.0.0")
```

**Step 2: Update pkg-config to find OBS 30+**

The existing `pkg_check_modules(LIBOBS REQUIRED libobs)` should work, but add a version check after it:

```cmake
pkg_check_modules(LIBOBS REQUIRED libobs)

# Verify OBS version
if(LIBOBS_VERSION VERSION_LESS ${OBS_MIN_VERSION})
    message(FATAL_ERROR "OBS Studio ${OBS_MIN_VERSION} or higher required. Found: ${LIBOBS_VERSION}")
endif()
```

**Step 3: Commit**

```bash
git add obs-snapfilter-plugin/CMakeLists.txt
git commit -m "build: require OBS 30+ and add version check"
```

---

## Task 9: Test Build on Local System

**Files:**
- None (verification only)

**Step 1: Install dependencies (macOS)**

```bash
brew install obs-studio opencv jsoncpp pkg-config cmake
```

**Step 2: Clean and rebuild**

```bash
cd obs-snapfilter-plugin
rm -rf build
mkdir build && cd build
cmake .. 2>&1 | tee cmake_output.txt
```

**Step 3: Check for errors**

```bash
grep -i "error" cmake_output.txt || echo "No errors found"
```

**Step 4: Build if CMake succeeded**

```bash
make 2>&1 | tee make_output.txt
```

**Step 5: Document any remaining issues**

If there are errors, note them for the next task.

---

## Task 10: Create Installation Instructions

**Files:**
- Modify: `obs-snapfilter-plugin/STATUS.md`

**Step 1: Update STATUS.md to reflect fixed state**

Replace the content with updated status showing the plugin now works with OBS 30+.

**Step 2: Commit all changes**

```bash
git add -A
git commit -m "docs: update STATUS.md for OBS 30+ compatibility"
```

---

## Verification Checklist

After all tasks:

- [ ] `snap-filter.h` uses `struct vec2` and `struct vec4`
- [ ] All `gs_effect_set_vec*` calls pass pointers (`&filter->face_center`)
- [ ] `render_filter` uses `obs_source_process_filter_begin/end`
- [ ] No `float[]` arrays remain for face/tint data
- [ ] CMake configures without type errors
- [ ] Plugin compiles (linker may still need OBS dev libs)

---

## Dependencies for Full Build

To actually test the plugin, you need:

- **macOS**: `brew install obs-studio` (installs dev headers)
- **Linux**: `sudo apt install obs-studio libobs-dev`
- **Windows**: OBS Studio SDK from GitHub releases

The plugin also requires OpenCV (`opencv4`) and jsoncpp.
