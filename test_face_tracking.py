#!/usr/bin/env python3
"""
Test script for Snap Camera Filter face tracking
Verifies OpenCV, face detection, and filter effects work correctly
"""

import cv2
import numpy as np
from PIL import Image
import sys

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import cv2
        print(f"  ✓ OpenCV version: {cv2.__version__}")
        
        import numpy as np
        print(f"  ✓ NumPy version: {np.__version__}")
        
        from PIL import Image
        print(f"  ✓ Pillow installed")
        
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False

def test_cascade_loading():
    """Test loading face detection cascade"""
    print("\nTesting cascade loading...")
    
    # Try cv2 package data path first
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    print(f"  Trying: {cascade_path}")
    
    try:
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if not face_cascade.empty():
            print(f"  ✓ Successfully loaded face cascade")
            return face_cascade
        else:
            print(f"  ✗ Cascade loaded but is empty")
            return None
    except Exception as e:
        print(f"  ✗ Error loading cascade: {e}")
        return None

def test_face_detection(face_cascade):
    """Test face detection on a sample image"""
    print("\nTesting face detection...")
    
    # Create a test image with a simple face-like pattern
    # (Just for testing cascade, won't detect without real face)
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    test_image[:, :] = (128, 128, 128)  # Gray background
    
    # Add some circles to simulate a face (won't actually be detected, just testing pipeline)
    cv2.circle(test_image, (320, 200), 50, (200, 200, 200), -1)  # Head
    cv2.circle(test_image, (290, 180), 10, (50, 50, 50), -1)    # Left eye
    cv2.circle(test_image, (350, 180), 10, (50, 50, 50), -1)    # Right eye
    
    gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
    
    try:
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        print(f"  ✓ Face detection executed (found {len(faces)} faces)")
        print(f"    (Note: Test pattern may not trigger detection, this is OK)")
        return True
    except Exception as e:
        print(f"  ✗ Face detection error: {e}")
        return False

def test_filters():
    """Test basic filter operations"""
    print("\nTesting filter effects...")
    
    # Create test image
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    try:
        # Test blur
        blurred = cv2.GaussianBlur(test_image, (15, 15), 0)
        print(f"  ✓ Gaussian blur")
        
        # Test edge detection
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        print(f"  ✓ Edge detection")
        
        # Test color conversion
        hsv = cv2.cvtColor(test_image, cv2.COLOR_BGR2HSV)
        print(f"  ✓ Color space conversion")
        
        # Test blending
        blended = cv2.addWeighted(test_image, 0.5, blurred, 0.5, 0)
        print(f"  ✓ Image blending")
        
        return True
    except Exception as e:
        print(f"  ✗ Filter error: {e}")
        return False

def main():
    print("=" * 60)
    print("Snap Camera Filter - Component Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    
    face_cascade = test_cascade_loading()
    results.append(("Cascade Loading", face_cascade is not None))
    
    if face_cascade:
        results.append(("Face Detection", test_face_detection(face_cascade)))
    else:
        results.append(("Face Detection", False))
        print("  ⚠ Skipped (cascade not loaded)")
    
    results.append(("Filter Effects", test_filters()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed! Script is ready for OBS.")
        return 0
    else:
        print("\n✗ Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
