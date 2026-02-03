// Default Snap Camera Filter Shader for OBS
// This shader provides basic face-tracking overlay effects

uniform texture2d image;
uniform float2 uv_scale;
uniform float2 uv_offset;
uniform float2 uv_size;
uniform float elapsed_time;
uniform float2 uv_pixel_interval;

// Face tracking data
uniform bool face_detected;
uniform float2 face_center;
uniform float2 face_size;
uniform float face_rotation;
uniform float face_confidence;

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
> = {1.0, 1.0, 1.0, 1.0};

uniform bool use_face_mask<
    string label = "Enable Face Mask";
> = true;

uniform float smooth_edges<
    string label = "Edge Smoothness";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.01;
> = 0.3;

uniform float glow_radius<
    string label = "Glow Radius";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 0.1;
    float step = 0.001;
> = 0.02;

uniform float glow_intensity<
    string label = "Glow Intensity";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 2.0;
    float step = 0.01;
> = 0.5;

sampler_state textureSampler {
    Filter = Linear;
    AddressU = Clamp;
    AddressV = Clamp;
};

struct VertData {
    float4 pos : POSITION;
    float2 uv : TEXCOORD0;
};

VertData VSDefault(VertData v_in) {
    VertData vert_out;
    vert_out.pos = mul(float4(v_in.pos.xyz, 1.0), ViewProj);
    vert_out.uv = v_in.uv * uv_scale + uv_offset;
    return vert_out;
}

float2 rotateUV(float2 uv, float2 center, float angle) {
    float2 delta = uv - center;
    float s = sin(angle);
    float c = cos(angle);
    float2 rotated = float2(
        delta.x * c - delta.y * s,
        delta.x * s + delta.y * c
    );
    return center + rotated;
}

float4 applyGlow(float4 color, float2 uv, texture2d tex) {
    float4 glow = float4(0.0, 0.0, 0.0, 0.0);
    float samples = 8.0;
    
    for(float i = 0.0; i < samples; i++) {
        float angle = (i / samples) * 6.28318;
        float2 offset = float2(cos(angle), sin(angle)) * glow_radius;
        glow += tex.Sample(textureSampler, uv + offset);
    }
    
    glow /= samples;
    return lerp(color, glow, glow_intensity * (1.0 - color.a));
}

float4 applyFaceEffect(float4 color, float2 uv) {
    if (!face_detected || !use_face_mask) {
        return color;
    }
    
    // Rotate UV to match face orientation
    float2 rotated_uv = rotateUV(uv, face_center, -face_rotation);
    float2 face_uv = face_center;
    
    // Calculate distance from face center (ellipse)
    float2 delta = rotated_uv - face_uv;
    float ellipse_dist = length(float2(
        delta.x / (face_size.x * 0.5),
        delta.y / (face_size.y * 0.5)
    ));
    
    // Create face mask with smooth edges
    float mask = 1.0 - smoothstep(0.8 - smooth_edges, 1.0 + smooth_edges, ellipse_dist);
    
    // Apply tint and intensity within face region
    float3 tinted = lerp(color.rgb, color.rgb * tint_color.rgb, mask * filter_intensity);
    float alpha = lerp(color.a, color.a * tint_color.a, mask * filter_intensity);
    
    return float4(tinted, alpha);
}

float4 mainImage(VertData v_in) : TARGET {
    float2 uv = v_in.uv;
    float4 color = image.Sample(textureSampler, uv);
    
    // Apply glow effect
    color = applyGlow(color, uv, image);
    
    // Apply face-tracked effects
    color = applyFaceEffect(color, uv);
    
    // Subtle overall color grading
    float3 graded = color.rgb;
    graded = pow(graded, float3(0.9, 0.95, 1.0)); // Temperature shift
    graded = saturate(graded * 1.05); // Slight brightness boost
    
    return float4(graded, color.a);
}

technique Draw {
    pass {
        vertex_shader = VSDefault(v_in);
        pixel_shader = mainImage(v_in);
    }
}
