// Beauty Filter - Skin smoothing and enhancement
// Replicates Snap Camera's popular beauty filters

uniform texture2d image;
uniform float2 uv_size;
uniform float elapsed_time;

// Face tracking
uniform bool face_detected;
uniform float2 face_center;
uniform float2 face_size;

// Beauty parameters
uniform float smooth_amount<
    string label = "Skin Smoothing";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.01;
> = 0.5;

uniform float whitening<
    string label = "Skin Whitening";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.01;
> = 0.3;

uniform float eye_enlargement<
    string label = "Eye Enlargement";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.01;
> = 0.2;

uniform float face_slimming<
    string label = "Face Slimming";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 1.0;
    float step = 0.01;
> = 0.0;

uniform float brightness<
    string label = "Brightness";
    string widget_type = "slider";
    float minimum = -0.5;
    float maximum = 0.5;
    float step = 0.01;
> = 0.0;

uniform float contrast<
    string label = "Contrast";
    string widget_type = "slider";
    float minimum = -0.5;
    float maximum = 0.5;
    float step = 0.01;
> = 0.0;

sampler_state textureSampler {
    Filter = Linear;
    AddressU = Clamp;
    AddressV = Clamp;
};

// Simple box blur for skin smoothing
float4 boxBlur(texture2d tex, float2 uv, float2 pixel_size, int radius) {
    float4 color = float4(0.0, 0.0, 0.0, 0.0);
    float samples = 0.0;
    
    for(int x = -radius; x <= radius; x++) {
        for(int y = -radius; y <= radius; y++) {
            float2 offset = float2(x, y) * pixel_size;
            color += tex.Sample(textureSampler, uv + offset);
            samples += 1.0;
        }
    }
    
    return color / samples;
}

// Detect skin tone (simple version)
float skinMask(float3 color) {
    float r = color.r;
    float g = color.g;
    float b = color.b;
    
    // Skin detection based on RGB ratios
    float rg = r - g;
    float rb = r - b;
    
    return smoothstep(0.0, 0.3, rg) * smoothstep(-0.2, 0.2, rb);
}

// Apply brightness and contrast
float3 adjustBrightnessContrast(float3 color, float bright, float cont) {
    color = color + bright;
    color = (color - 0.5) * (1.0 + cont) + 0.5;
    return saturate(color);
}

// Skin whitening
float3 applyWhitening(float3 color, float amount) {
    float luminance = dot(color, float3(0.299, 0.587, 0.114));
    float3 white = float3(1.0, 1.0, 1.0);
    return lerp(color, white, amount * (1.0 - luminance) * 0.3);
}

float4 mainImage(VertData v_in) : TARGET {
    float2 uv = v_in.uv;
    float2 pixel_size = 1.0 / uv_size;
    
    float4 color = image.Sample(textureSampler, uv);
    float4 original = color;
    
    if (!face_detected) {
        // Apply global adjustments even without face detection
        color.rgb = adjustBrightnessContrast(color.rgb, brightness, contrast);
        return color;
    }
    
    // Calculate face region mask
    float2 face_dist = abs(uv - face_center) / (face_size * 0.6);
    float face_mask = smoothstep(1.2, 0.8, length(face_dist));
    
    // Skin smoothing within face region
    if (smooth_amount > 0.0 && face_mask > 0.0) {
        float4 blurred = boxBlur(image, uv, pixel_size, 2);
        float skin = skinMask(color.rgb);
        float smooth_factor = smooth_amount * skin * face_mask;
        color = lerp(color, blurred, smooth_factor);
    }
    
    // Skin whitening
    if (whitening > 0.0 && face_mask > 0.0) {
        float skin = skinMask(color.rgb);
        color.rgb = applyWhitening(color.rgb, whitening * skin * face_mask);
    }
    
    // Global adjustments
    color.rgb = adjustBrightnessContrast(color.rgb, brightness, contrast);
    
    // Preserve original alpha
    color.a = original.a;
    
    return saturate(color);
}
