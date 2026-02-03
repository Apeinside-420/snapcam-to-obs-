#!/usr/bin/env python3
"""
Snap Camera Filter - Python OBS Script
Provides face tracking and filter effects for OBS Studio

Installation:
1. Copy this file to OBS scripts folder:
   - Windows: %APPDATA%\obs-studio\scripts\
   - Linux: ~/.config/obs-studio/scripts/
   - macOS: ~/Library/Application Support/obs-studio/scripts/
2. Enable Python scripting in OBS: Tools > Scripts > Python Settings
3. Load this script in OBS Script dialog
"""

import obspython as obs
import cv2
import numpy as np
from PIL import Image
import threading
import queue
import time
import json
import os
from pathlib import Path

# Script metadata
SCRIPT_NAME = "Snap Camera Filter (Python)"
SCRIPT_VERSION = "1.0.0"
SCRIPT_DESCRIPTION = "Face tracking and filter effects for OBS"

# Global variables
face_cascade = None
eye_cascade = None
face_data = {
    'detected': False,
    'center_x': 0.5,
    'center_y': 0.5,
    'width': 0.0,
    'height': 0.0,
    'rotation': 0.0,
    'confidence': 0.0
}
tracking_thread = None
tracking_queue = queue.Queue()
should_exit = False
filter_sources = {}

# Source callbacks
def script_description():
    return SCRIPT_DESCRIPTION

def script_properties():
    props = obs.obs_properties_create()
    
    # Info
    obs.obs_properties_add_text(props, "info", "Info", obs.OBS_TEXT_INFO)
    
    # Face tracking toggle
    obs.obs_properties_add_bool(props, "enable_tracking", "Enable Face Tracking")
    
    # Filter intensity
    intensity = obs.obs_properties_add_float_slider(
        props, "intensity", "Filter Intensity", 0.0, 1.0, 0.01
    )
    obs.obs_property_set_default_value(intensity, 0.5)
    
    # Effect type
    effect_list = obs.obs_properties_add_list(
        props, "effect_type", "Effect Type", 
        obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING
    )
    obs.obs_property_list_add_string(effect_list, "Beauty (Skin Smooth)", "beauty")
    obs.obs_property_list_add_string(effect_list, "Cartoon", "cartoon")
    obs.obs_property_list_add_string(effect_list, "Face Glow", "glow")
    obs.obs_property_list_add_string(effect_list, "Color Tint", "tint")
    obs.obs_property_list_add_string(effect_list, "Edge Detection", "edge")
    obs.obs_property_list_add_string(effect_list, "Blur", "blur")
    
    # Color tint
    color = obs.obs_properties_add_color(props, "tint_color", "Tint Color")
    obs.obs_property_set_default_value(color, 0xFFFFFFFF)
    
    # Smoothing
    smooth = obs.obs_properties_add_float_slider(
        props, "smoothing", "Tracking Smoothness", 0.0, 1.0, 0.01
    )
    obs.obs_property_set_default_value(smooth, 0.3)
    
    # Detection confidence
    confidence = obs.obs_properties_add_float_slider(
        props, "confidence", "Detection Confidence", 0.0, 1.0, 0.01
    )
    obs.obs_property_set_default_value(confidence, 0.5)
    
    # Lens file selector
    lens_path = obs.obs_properties_add_path(
        props, "lens_file", "Lens File (Optional)", 
        obs.OBS_PATH_FILE, "Lens files (*.lns *.zip *.json);;All files (*.*)", 
        ""
    )
    
    return props

def script_defaults(settings):
    obs.obs_data_set_default_bool(settings, "enable_tracking", True)
    obs.obs_data_set_default_double(settings, "intensity", 0.5)
    obs.obs_data_set_default_string(settings, "effect_type", "beauty")
    obs.obs_data_set_default_int(settings, "tint_color", 0xFFFFFFFF)
    obs.obs_data_set_default_double(settings, "smoothing", 0.3)
    obs.obs_data_set_default_double(settings, "confidence", 0.5)

def script_load(settings):
    global face_cascade, eye_cascade, should_exit
    
    print(f"[{SCRIPT_NAME}] Loading script...")
    
    # Initialize face detection
    try:
        # Try to load Haar cascades from various locations
        cascade_paths = [
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml",  # cv2 package data
            "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
            "/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
            "/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        ]
        
        cascade_loaded = False
        for path in cascade_paths:
            if os.path.exists(path):
                face_cascade = cv2.CascadeClassifier(path)
                if not face_cascade.empty():
                    print(f"[{SCRIPT_NAME}] Loaded face cascade from: {path}")
                    cascade_loaded = True
                    break
        
        if not cascade_loaded:
            print(f"[{SCRIPT_NAME}] Warning: Could not load face detection cascade")
            print(f"[{SCRIPT_NAME}] Please install: sudo apt-get install opencv-data")
            return
            
    except Exception as e:
        print(f"[{SCRIPT_NAME}] Error initializing face detection: {e}")
        return
    
    # Start tracking thread
    should_exit = False
    tracking_thread = threading.Thread(target=tracking_loop)
    tracking_thread.daemon = True
    tracking_thread.start()
    
    print(f"[{SCRIPT_NAME}] Script loaded successfully")

def script_unload():
    global should_exit
    
    print(f"[{SCRIPT_NAME}] Unloading script...")
    should_exit = True
    
    if tracking_thread and tracking_thread.is_alive():
        tracking_thread.join(timeout=1.0)
    
    print(f"[{SCRIPT_NAME}] Script unloaded")

def tracking_loop():
    """Background thread for face detection"""
    global face_data, should_exit
    
    print(f"[{SCRIPT_NAME}] Face tracking thread started")
    
    while not should_exit:
        try:
            # Get frame from queue (non-blocking)
            try:
                frame_data = tracking_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            if frame_data is None:
                continue
            
            # Process frame for face detection
            if face_cascade is not None:
                detect_faces(frame_data)
                
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Tracking error: {e}")
            time.sleep(0.1)
    
    print(f"[{SCRIPT_NAME}] Face tracking thread stopped")

def detect_faces(frame):
    """Detect faces in a frame and update global face_data"""
    global face_data
    
    try:
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80)
        )
        
        if len(faces) > 0:
            # Use largest face
            main_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = main_face
            
            # Calculate normalized coordinates
            height, width = frame.shape[:2]
            
            # Smooth the data
            alpha = face_data.get('smoothing', 0.3)
            new_center_x = (x + w / 2) / width
            new_center_y = (y + h / 2) / height
            new_width = w / width
            new_height = h / height
            
            face_data['center_x'] = face_data.get('center_x', 0.5) * (1 - alpha) + new_center_x * alpha
            face_data['center_y'] = face_data.get('center_y', 0.5) * (1 - alpha) + new_center_y * alpha
            face_data['width'] = face_data.get('width', 0) * (1 - alpha) + new_width * alpha
            face_data['height'] = face_data.get('height', 0) * (1 - alpha) + new_height * alpha
            face_data['detected'] = True
            face_data['confidence'] = 0.8
        else:
            face_data['detected'] = False
            face_data['confidence'] = 0.0
            
    except Exception as e:
        print(f"[{SCRIPT_NAME}] Face detection error: {e}")

# Filter class
class SnapFilter:
    def __init__(self, source, settings):
        self.source = source
        self.settings = settings
        self.effect_type = "beauty"
        self.intensity = 0.5
        self.tint_color = [1.0, 1.0, 1.0, 1.0]
        self.smoothing = 0.3
        self.enable_tracking = True
        self.lens_data = None
        
        # Load lens if specified
        self.load_lens()
    
    def load_lens(self):
        lens_file = obs.obs_data_get_string(self.settings, "lens_file")
        if lens_file:
            try:
                with open(lens_file, 'r') as f:
                    self.lens_data = json.load(f)
                    print(f"[{SCRIPT_NAME}] Loaded lens: {self.lens_data.get('name', 'Unknown')}")
            except Exception as e:
                print(f"[{SCRIPT_NAME}] Error loading lens: {e}")
    
    def update(self, settings):
        self.settings = settings
        self.enable_tracking = obs.obs_data_get_bool(settings, "enable_tracking")
        self.intensity = obs.obs_data_get_double(settings, "intensity")
        self.effect_type = obs.obs_data_get_string(settings, "effect_type")
        self.smoothing = obs.obs_data_get_double(settings, "smoothing")
        
        # Get tint color
        color_int = obs.obs_data_get_int(settings, "tint_color")
        self.tint_color[0] = ((color_int >> 16) & 0xFF) / 255.0
        self.tint_color[1] = ((color_int >> 8) & 0xFF) / 255.0
        self.tint_color[2] = (color_int & 0xFF) / 255.0
        self.tint_color[3] = ((color_int >> 24) & 0xFF) / 255.0
    
    def process_frame(self, frame):
        """Apply filter effects to a frame"""
        if frame is None:
            return None
        
        try:
            # Convert OBS frame to OpenCV format
            # Frame comes as numpy array from OBS
            
            # Apply effect based on type
            if self.effect_type == "beauty":
                frame = self.apply_beauty(frame)
            elif self.effect_type == "cartoon":
                frame = self.apply_cartoon(frame)
            elif self.effect_type == "glow":
                frame = self.apply_glow(frame)
            elif self.effect_type == "tint":
                frame = self.apply_tint(frame)
            elif self.effect_type == "edge":
                frame = self.apply_edge(frame)
            elif self.effect_type == "blur":
                frame = self.apply_blur(frame)
            
            # Apply face-tracked effects if enabled and face detected
            if self.enable_tracking and face_data['detected']:
                frame = self.apply_face_effect(frame)
            
            return frame
            
        except Exception as e:
            print(f"[{SCRIPT_NAME}] Filter error: {e}")
            return frame
    
    def apply_beauty(self, frame):
        """Apply skin smoothing effect"""
        intensity = self.intensity
        
        # Create skin mask
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define skin color range
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Apply bilateral filter for smoothing
        smoothed = cv2.bilateralFilter(frame, 9, 75, 75)
        
        # Blend based on skin mask
        skin_mask = skin_mask.astype(float) / 255.0 * intensity
        skin_mask = np.stack([skin_mask] * 3, axis=2)
        
        result = (frame * (1 - skin_mask) + smoothed * skin_mask).astype(np.uint8)
        
        # Subtle brightness increase
        result = cv2.convertScaleAbs(result, alpha=1.0 + intensity * 0.1, beta=intensity * 10)
        
        return result
    
    def apply_cartoon(self, frame):
        """Apply cartoon effect"""
        intensity = self.intensity
        
        # Edge detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.medianBlur(gray, 7)
        edges = cv2.adaptiveThreshold(
            gray_blur, 255, 
            cv2.ADAPTIVE_THRESH_MEAN_C, 
            cv2.THRESH_BINARY, 
            9, 2
        )
        
        # Color quantization
        color = frame.copy()
        Z = color.reshape((-1, 3))
        Z = np.float32(Z)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        K = 8
        _, labels, centers = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()]
        quantized = quantized.reshape((color.shape))
        
        # Combine edges with quantized colors
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        result = cv2.bitwise_and(quantized, edges)
        
        # Blend with original based on intensity
        result = cv2.addWeighted(frame, 1 - intensity, result, intensity, 0)
        
        return result
    
    def apply_glow(self, frame):
        """Apply glow effect centered on face"""
        intensity = self.intensity
        
        # Blur the frame
        blurred = cv2.GaussianBlur(frame, (21, 21), 0)
        
        # Create mask if face detected
        if face_data['detected']:
            h, w = frame.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            
            # Draw ellipse at face position
            center = (
                int(face_data['center_x'] * w),
                int(face_data['center_y'] * h)
            )
            axes = (
                int(face_data['width'] * w * 0.6),
                int(face_data['height'] * h * 0.6)
            )
            
            cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
            
            # Blur mask edges
            mask = cv2.GaussianBlur(mask, (51, 51), 0)
            mask = mask.astype(float) / 255.0 * intensity
            mask = np.stack([mask] * 3, axis=2)
            
            # Apply glow only to face region
            result = (frame * (1 - mask) + blurred * mask).astype(np.uint8)
        else:
            # Subtle overall glow
            result = cv2.addWeighted(frame, 1.0, blurred, intensity * 0.3, 0)
        
        return result
    
    def apply_tint(self, frame):
        """Apply color tint"""
        tint = np.array(self.tint_color[:3]) * 255
        intensity = self.intensity
        
        # Create tint overlay
        tinted = frame * (1 - intensity) + tint * intensity
        
        return tinted.astype(np.uint8)
    
    def apply_edge(self, frame):
        """Apply edge detection"""
        intensity = self.intensity
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # Invert edges for better look
        edges = 255 - edges
        
        # Blend with original
        result = cv2.addWeighted(frame, 1 - intensity, edges, intensity, 0)
        
        return result
    
    def apply_blur(self, frame):
        """Apply Gaussian blur"""
        intensity = self.intensity
        
        if intensity > 0.01:
            kernel_size = int(21 * intensity)
            if kernel_size % 2 == 0:
                kernel_size += 1
            kernel_size = max(3, min(kernel_size, 31))
            
            result = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
            
            # Blend with original
            result = cv2.addWeighted(frame, 1 - intensity, result, intensity, 0)
            return result
        
        return frame
    
    def apply_face_effect(self, frame):
        """Apply effects specifically to face region"""
        if not face_data['detected']:
            return frame
        
        h, w = frame.shape[:2]
        
        # Calculate face region
        cx = int(face_data['center_x'] * w)
        cy = int(face_data['center_y'] * h)
        fw = int(face_data['width'] * w)
        fh = int(face_data['height'] * h)
        
        # Create mask for face region
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(mask, (cx, cy), (fw//2, fh//2), 
                   np.degrees(face_data.get('rotation', 0)), 
                   0, 360, 255, -1)
        
        # Blur mask edges
        mask = cv2.GaussianBlur(mask, (51, 51), 0)
        mask = mask.astype(float) / 255.0
        
        # Example: brighten face region
        brightened = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)
        
        # Blend based on mask
        mask_3ch = np.stack([mask] * 3, axis=2)
        result = (frame * (1 - mask_3ch * 0.5) + brightened * mask_3ch * 0.5).astype(np.uint8)
        
        return result

# OBS Filter callbacks
filter_instance = None

def filter_create(settings, source):
    global filter_instance
    filter_instance = SnapFilter(source, settings)
    print(f"[{SCRIPT_NAME}] Filter created")
    return filter_instance

def filter_destroy(filter_obj):
    global filter_instance
    if filter_obj:
        print(f"[{SCRIPT_NAME}] Filter destroyed")
        filter_instance = None

def filter_update(filter_obj, settings):
    if filter_obj:
        filter_obj.update(settings)

def filter_get_properties(filter_obj):
    return script_properties()

def filter_get_defaults(settings):
    script_defaults(settings)

def filter_video_render(filter_obj, effect):
    """Render callback - processes the frame"""
    if not filter_obj:
        return
    
    target = obs.obs_filter_get_target(filter_obj.source)
    if not target:
        obs.obs_source_skip_video_filter(filter_obj.source)
        return
    
    # Get the source output
    width = obs.obs_source_get_base_width(target)
    height = obs.obs_source_get_base_height(target)
    
    # Capture the frame (simplified - in reality this needs proper texture handling)
    # For now, this is a placeholder showing the structure
    # Full implementation would require proper OBS graphics API usage
    
    # Render the source
    obs.obs_source_video_render(target)

def filter_video_tick(filter_obj, seconds):
    pass

# Script update callback
def script_update(settings):
    """Called when script settings are updated"""
    # Update global face tracking settings
    global face_data
    face_data['smoothing'] = obs.obs_data_get_double(settings, "smoothing")
    
    # Update all active filters
    for source_id, filter_obj in filter_sources.items():
        if filter_obj:
            filter_obj.update(settings)

# Note: script_load and script_unload are already defined at the top of the file
