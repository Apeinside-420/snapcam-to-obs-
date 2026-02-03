#!/usr/bin/env python3
"""
Snap Lens Converter - Extracts and converts Snap Camera lenses for OBS use

Snap lenses are typically .zip files with .lns extension containing:
- lens.json (metadata)
- textures/ (PNG/JPG textures)
- shaders/ (GLSL shaders)
- models/ (3D models in proprietary format)
- audio/ (sound effects)
- scripts/ (JavaScript/TypeScript logic)
"""

import os
import sys
import json
import struct
import zipfile
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LensMetadata:
    name: str
    description: str
    version: str
    author: str
    category: str
    preview_image: Optional[str] = None
    face_tracking: bool = False
    uses_audio: bool = False
    uses_3d: bool = False

class SnapLensExtractor:
    """Extracts and converts Snap Camera lens files"""
    
    def __init__(self, output_dir: str = "extracted"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_lens(self, lens_path: str) -> Optional[LensMetadata]:
        """Extract a .lns or .zip lens file"""
        lens_path_obj = Path(lens_path)
        
        if not lens_path_obj.exists():
            logger.error(f"Lens file not found: {lens_path}")
            return None
            
        lens_name = lens_path_obj.stem
        extract_dir = self.output_dir / lens_name
        
        try:
            # Extract the zip/lns file
            with zipfile.ZipFile(lens_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            logger.info(f"Extracted {lens_path} to {extract_dir}")
            
            # Parse metadata
            metadata = self._parse_metadata(extract_dir)
            
            # Convert assets
            self._convert_textures(extract_dir)
            self._convert_shaders(extract_dir)
            self._convert_models(extract_dir)
            
            # Generate OBS shader files
            self._generate_obs_shaders(extract_dir, metadata)
            
            logger.info(f"Successfully processed lens: {metadata.name}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract {lens_path}: {e}")
            return None
    
    def _parse_metadata(self, extract_dir: Path) -> LensMetadata:
        """Parse lens.json or Info.plist for metadata"""
        lens_json = extract_dir / "lens.json"
        
        if lens_json.exists():
            with open(lens_json, 'r') as f:
                data = json.load(f)
                
            return LensMetadata(
                name=data.get('name', 'Unknown'),
                description=data.get('description', ''),
                version=data.get('version', '1.0'),
                author=data.get('author', 'Unknown'),
                category=data.get('category', 'general'),
                face_tracking=data.get('face_tracking', False),
                uses_audio=data.get('uses_audio', False),
                uses_3d=data.get('uses_3d', False)
            )
        
        # Fallback metadata
        return LensMetadata(
            name=extract_dir.name,
            description="",
            version="1.0",
            author="Unknown",
            category="general"
        )
    
    def _convert_textures(self, extract_dir: Path):
        """Convert textures to OBS-compatible formats"""
        textures_dir = extract_dir / "textures"
        output_dir = extract_dir / "obs_assets" / "textures"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not textures_dir.exists():
            return
            
        for texture_file in textures_dir.glob("*"):
            if texture_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                # Copy to output, converting webp to png if needed
                if texture_file.suffix.lower() == '.webp':
                    try:
                        from PIL import Image
                        img = Image.open(texture_file)
                        output_path = output_dir / f"{texture_file.stem}.png"
                        img.save(output_path, 'PNG')
                        logger.info(f"Converted {texture_file.name} to PNG")
                    except ImportError:
                        logger.warning("PIL not installed, skipping webp conversion")
                        shutil.copy2(texture_file, output_dir / texture_file.name)
                else:
                    shutil.copy2(texture_file, output_dir / texture_file.name)
    
    def _convert_shaders(self, extract_dir: Path):
        """Convert GLSL shaders to OBS HLSL format"""
        shaders_dir = extract_dir / "shaders"
        output_dir = extract_dir / "obs_assets" / "shaders"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not shaders_dir.exists():
            return
            
        for shader_file in shaders_dir.glob("*.glsl"):
            obs_shader = self._glsl_to_hlsl(shader_file)
            output_path = output_dir / f"{shader_file.stem}.shader"
            with open(output_path, 'w') as f:
                f.write(obs_shader)
            logger.info(f"Converted shader: {shader_file.name}")
    
    def _glsl_to_hlsl(self, shader_path: Path) -> str:
        """Convert GLSL shader to OBS HLSL format"""
        with open(shader_path, 'r') as f:
            glsl_code = f.read()
        
        # Basic conversions
        hlsl_code = glsl_code
        
        # Replace GLSL types with HLSL
        type_mappings = {
            'vec2': 'float2',
            'vec3': 'float3',
            'vec4': 'float4',
            'mat2': 'float2x2',
            'mat3': 'float3x3',
            'mat4': 'float4x4',
            'sampler2D': 'texture2d',
            'texture2D': 'image.Sample',
            'gl_FragCoord': 'uv',
            'gl_FragColor': 'output_color',
        }
        
        for glsl, hlsl in type_mappings.items():
            hlsl_code = hlsl_code.replace(glsl, hlsl)
        
        # Add OBS shader template
        obs_template = '''// Converted from Snap Lens shader
uniform texture2d image;
uniform float2 uv_size;
uniform float elapsed_time;
uniform float4x4 ViewProj;

// Face tracking uniforms (if available)
uniform float2 face_position;
uniform float2 face_size;
uniform float face_rotation;

float4 mainImage(VertData v_in) : TARGET
{
    float2 uv = v_in.uv;
    float4 output_color = image.Sample(textureSampler, uv);
    
'''
        
        obs_footer = '''
    return output_color;
}
'''
        
        # Extract main function body
        if 'void main()' in hlsl_code:
            start = hlsl_code.find('void main()')
            body_start = hlsl_code.find('{', start) + 1
            body_end = hlsl_code.rfind('}')
            main_body = hlsl_code[body_start:body_end]
            
            return obs_template + main_body + obs_footer
        
        return obs_template + hlsl_code + obs_footer
    
    def _convert_models(self, extract_dir: Path):
        """Convert 3D models if possible"""
        models_dir = extract_dir / "models"
        if not models_dir.exists():
            return
            
        logger.info("3D model conversion not yet implemented (proprietary format)")
    
    def _generate_obs_shaders(self, extract_dir: Path, metadata: LensMetadata):
        """Generate OBS-compatible shader files with face tracking support"""
        output_dir = extract_dir / "obs_assets"
        
        # Create main filter shader
        main_shader = self._generate_face_tracking_shader(metadata)
        
        with open(output_dir / "snap_filter.shader", 'w') as f:
            f.write(main_shader)
        
        # Create info file
        info = {
            'name': metadata.name,
            'description': metadata.description,
            'face_tracking': metadata.face_tracking,
            'files': {
                'main_shader': 'snap_filter.shader',
                'textures': [t.name for t in (output_dir / 'textures').glob('*')] if (output_dir / 'textures').exists() else []
            }
        }
        
        with open(output_dir / 'lens_info.json', 'w') as f:
            json.dump(info, f, indent=2)
    
    def _generate_face_tracking_shader(self, metadata: LensMetadata) -> str:
        """Generate a shader template with face tracking support"""
        return '''// Snap Camera Filter for OBS
// Converted from: {name}
// Face Tracking: {face_tracking}

uniform texture2d image;
uniform float2 uv_size;
uniform float elapsed_time;
uniform float4x4 ViewProj;
uniform float2 uv_scale;
uniform float2 uv_offset;

// Face tracking data (provided by plugin)
uniform bool face_detected;
uniform float2 face_center;      // Normalized 0-1
uniform float2 face_size;        // Width, height in UV space
uniform float face_rotation;     // Rotation in radians
uniform float face_confidence;   // 0-1 detection confidence

// Feature points (if available)
uniform float2 left_eye;
uniform float2 right_eye;
uniform float2 nose_tip;
uniform float2 mouth_center;
uniform float2 chin;

// Filter parameters
uniform float filter_intensity<
    string label = "Filter Intensity";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.01;
> = 0.5;

uniform float4 tint_color<
    string label = "Tint Color";
> = {{ 1.0, 1.0, 1.0, 1.0 }};

uniform bool use_face_mask<
    string label = "Enable Face Mask";
> = true;

float2 rotateUV(float2 uv, float2 center, float angle) {{
    float2 delta = uv - center;
    float s = sin(angle);
    float c = cos(angle);
    float2 rotated = float2(
        delta.x * c - delta.y * s,
        delta.x * s + delta.y * c
    );
    return center + rotated;
}}

float4 applyFaceEffect(float4 color, float2 uv, VertData v_in) {{
    if (!face_detected || !use_face_mask) {{
        return color;
    }}
    
    // Calculate distance from face center
    float2 face_uv = face_center;
    float dist = distance(uv, face_uv);
    
    // Apply effect within face region
    float face_radius = max(face_size.x, face_size.y) * 0.6;
    float mask = smoothstep(face_radius, face_radius * 0.8, dist);
    
    // Blend with tint color
    float3 tinted = lerp(color.rgb, color.rgb * tint_color.rgb, mask * filter_intensity);
    
    return float4(tinted, color.a);
}}

float4 mainImage(VertData v_in) : TARGET {{
    float2 uv = v_in.uv;
    float4 color = image.Sample(textureSampler, uv);
    
    // Apply face-tracked effects
    color = applyFaceEffect(color, uv, v_in);
    
    // Add your custom effects here
    // This is where extracted lens effects would be applied
    
    return color;
}}
'''.format(
            name=metadata.name,
            face_tracking="enabled" if metadata.face_tracking else "disabled"
        )

def batch_convert(input_dir: str, output_dir: str):
    """Convert all lens files in a directory"""
    input_path = Path(input_dir)
    extractor = SnapLensExtractor(output_dir)
    
    lens_files = list(input_path.glob("*.lns")) + list(input_path.glob("*.zip"))
    
    logger.info(f"Found {len(lens_files)} lens files to convert")
    
    results = []
    for lens_file in lens_files:
        metadata = extractor.extract_lens(str(lens_file))
        results.append((lens_file.name, metadata))
    
    # Generate report
    report_path = Path(output_dir) / "conversion_report.json"
    report = {
        'total': len(lens_files),
        'successful': sum(1 for _, m in results if m is not None),
        'failed': sum(1 for _, m in results if m is None),
        'lenses': [
            {
                'file': name,
                'success': meta is not None,
                'name': meta.name if meta else None
            }
            for name, meta in results
        ]
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Conversion complete. Report saved to {report_path}")
    return report

def main():
    parser = argparse.ArgumentParser(description='Convert Snap Camera lenses to OBS format')
    parser.add_argument('input', help='Input lens file (.lns/.zip) or directory')
    parser.add_argument('-o', '--output', default='extracted', help='Output directory')
    parser.add_argument('--batch', action='store_true', help='Process all lenses in directory')
    
    args = parser.parse_args()
    
    if args.batch:
        batch_convert(args.input, args.output)
    else:
        extractor = SnapLensExtractor(args.output)
        metadata = extractor.extract_lens(args.input)
        
        if metadata:
            print(f"\\nConverted: {metadata.name}")
            print(f"Author: {metadata.author}")
            print(f"Face Tracking: {metadata.face_tracking}")
            print(f"Output: {Path(args.output) / metadata.name / 'obs_assets'}")
        else:
            print("Conversion failed!")
            sys.exit(1)

if __name__ == '__main__':
    main()
