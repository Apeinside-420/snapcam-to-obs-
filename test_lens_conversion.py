#!/usr/bin/env python3
"""
Test script for lens converter
Creates a sample lens and tests the conversion process
"""

import os
import sys
import json
import zipfile
import tempfile
import shutil
from pathlib import Path

# Add lens-converter to path
sys.path.insert(0, str(Path(__file__).parent / "lens-converter"))

def create_test_lens(output_path):
    """Create a test lens file with sample content"""
    print("Creating test lens file...")
    
    # Create temporary directory for lens content
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create lens.json metadata
        lens_metadata = {
            "name": "Test Beauty Filter",
            "description": "A simple beauty filter for testing",
            "version": "1.0",
            "author": "Test Author",
            "category": "beauty",
            "face_tracking": True,
            "uses_audio": False,
            "uses_3d": False
        }
        
        with open(temp_path / "lens.json", 'w') as f:
            json.dump(lens_metadata, f, indent=2)
        
        # Create textures directory with dummy texture
        textures_dir = temp_path / "textures"
        textures_dir.mkdir()
        
        # Create a simple test texture (1x1 white pixel)
        try:
            from PIL import Image
            img = Image.new('RGB', (64, 64), color='white')
            img.save(textures_dir / "test_texture.png")
            print("  ✓ Created test texture")
        except ImportError:
            # Create a dummy file if PIL not available
            (textures_dir / "test_texture.png").write_text("dummy")
            print("  ⚠ PIL not available, created dummy texture")
        
        # Create shaders directory with sample GLSL shader
        shaders_dir = temp_path / "shaders"
        shaders_dir.mkdir()
        
        sample_shader = """
// Simple beauty shader
varying vec2 vUv;
uniform sampler2D inputTexture;
uniform float smoothness;

void main() {
    vec4 color = texture2D(inputTexture, vUv);
    
    // Simple blur for beauty effect
    vec4 blurred = color;
    float offset = 0.002 * smoothness;
    
    blurred += texture2D(inputTexture, vUv + vec2(-offset, -offset));
    blurred += texture2D(inputTexture, vUv + vec2(offset, -offset));
    blurred += texture2D(inputTexture, vUv + vec2(-offset, offset));
    blurred += texture2D(inputTexture, vUv + vec2(offset, offset));
    blurred /= 5.0;
    
    gl_FragColor = blurred;
}
"""
        with open(shaders_dir / "beauty.glsl", 'w') as f:
            f.write(sample_shader)
        print("  ✓ Created test shader")
        
        # Create the zip file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
        
        print(f"  ✓ Created lens file: {output_path}")
        return True

def test_lens_converter():
    """Test the lens converter functionality"""
    print("=" * 60)
    print("Lens Converter Test")
    print("=" * 60)
    
    # Create test lens
    test_lens_path = "/tmp/test_beauty_filter.lns"
    if not create_test_lens(test_lens_path):
        print("✗ Failed to create test lens")
        return False
    
    print("\nTesting lens converter...")
    
    try:
        from snap_lens_converter import SnapLensExtractor
        
        # Create output directory
        output_dir = Path("/tmp/converted_lenses")
        if output_dir.exists():
            shutil.rmtree(output_dir)
        
        # Extract and convert
        extractor = SnapLensExtractor(str(output_dir))
        metadata = extractor.extract_lens(test_lens_path)
        
        if metadata:
            print(f"\n✓ Successfully converted lens: {metadata.name}")
            print(f"  Author: {metadata.author}")
            print(f"  Category: {metadata.category}")
            print(f"  Face tracking: {metadata.face_tracking}")
            
            # Check output files
            lens_output = output_dir / "test_beauty_filter"
            print(f"\nChecking output files in {lens_output}:")
            
            checks = [
                ("lens.json", lens_output / "lens.json"),
                ("OBS assets directory", lens_output / "obs_assets"),
                ("Converted textures", lens_output / "obs_assets" / "textures"),
                ("Converted shaders", lens_output / "obs_assets" / "shaders"),
            ]
            
            all_passed = True
            for name, path in checks:
                if path.exists():
                    print(f"  ✓ {name}")
                else:
                    print(f"  ✗ {name} (not found)")
                    all_passed = False
            
            # List converted files
            if (lens_output / "obs_assets").exists():
                print("\nConverted files:")
                for item in (lens_output / "obs_assets").rglob("*"):
                    if item.is_file():
                        rel_path = item.relative_to(lens_output / "obs_assets")
                        print(f"  - {rel_path}")
            
            return all_passed
        else:
            print("✗ Conversion failed")
            return False
            
    except Exception as e:
        print(f"✗ Error testing converter: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_lens_converter()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Lens converter test passed")
        print("\nYou can now convert real Snap Camera lenses:")
        print("  python3 lens-converter/snap_lens_converter.py <lens_file.lns> -o output/")
        return 0
    else:
        print("✗ Lens converter test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
