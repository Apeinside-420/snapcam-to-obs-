// Cartoon Filter - Edge detection and color quantization
// Creates a comic book / cartoon effect

uniform texture2d image;
uniform float2 uv_size;
uniform float2 uv_pixel_interval;

uniform float edge_threshold<
    string label = "Edge Threshold";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 2.0;
    float step = 0.01;
> = 0.3;

uniform float color_levels<
    string label = "Color Levels";
    string widget_type = "slider";
    float minimum = 2.0;
    float maximum = 32.0;
    float step = 1.0;
> = 8.0;

uniform float edge_intensity<
    string label = "Edge Intensity";
    string widget_type = "slider";
    float minimum = 0.0;
    float maximum = 2.0;
    float step = 0.01;
> = 1.0;

uniform float saturation_boost<
    string label = "Saturation Boost";
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

// Sobel edge detection
float sobelEdge(texture2d tex, float2 uv, float2 pixel_size) {
    float2 offsets[9] = {
        float2(-1, -1), float2(0, -1), float2(1, -1),
        float2(-1,  0), float2(0,  0), float2(1,  0),
        float2(-1,  1), float2(0,  1), float2(1,  1)
    };
    
    float sobelX[9] = {
        -1, 0, 1,
        -2, 0, 2,
        -1, 0, 1
    };
    
    float sobelY[9] = {
        -1, -2, -1,
         0,  0,  0,
         1,  2,  1
    };
    
    float edgeX = 0.0;
    float edgeY = 0.0;
    
    for(int i = 0; i < 9; i++) {
        float4 color = tex.Sample(textureSampler, uv + offsets[i] * pixel_size);
        float luminance = dot(color.rgb, float3(0.299, 0.587, 0.114));
        edgeX += luminance * sobelX[i];
        edgeY += luminance * sobelY[i];
    }
    
    return sqrt(edgeX * edgeX + edgeY * edgeY);
}

// RGB to HSV conversion
float3 rgb2hsv(float3 c) {
    float4 K = float4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    float4 p = lerp(float4(c.bg, K.wz), float4(c.gb, K.xy), step(c.b, c.g));
    float4 q = lerp(float4(p.xyw, c.r), float4(c.r, p.yzx), step(p.x, c.r));
    
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return float3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

// HSV to RGB conversion
float3 hsv2rgb(float3 c) {
    float4 K = float4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    float3 p = abs(frac(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * lerp(K.xxx, saturate(p - K.xxx), c.y);
}

// Quantize colors
float3 quantizeColor(float3 color, float levels) {
    float3 hsv = rgb2hsv(color);
    
    // Quantize hue, saturation, and value
    hsv.x = floor(hsv.x * levels) / levels;
    hsv.y = floor(hsv.y * (levels * 0.5)) / (levels * 0.5);
    hsv.z = floor(hsv.z * levels) / levels;
    
    return hsv2rgb(hsv);
}

float4 mainImage(VertData v_in) : TARGET {
    float2 uv = v_in.uv;
    float2 pixel_size = uv_pixel_interval;
    
    // Get original color
    float4 color = image.Sample(textureSampler, uv);
    
    // Detect edges
    float edge = sobelEdge(image, uv, pixel_size);
    edge = smoothstep(edge_threshold * 0.1, edge_threshold, edge);
    
    // Quantize colors
    float3 quantized = quantizeColor(color.rgb, color_levels);
    
    // Boost saturation
    float3 hsv = rgb2hsv(quantized);
    hsv.y = saturate(hsv.y * (1.0 + saturation_boost));
    quantized = hsv2rgb(hsv);
    
    // Apply edge overlay
    float3 edge_color = float3(0.0, 0.0, 0.0);
    float3 final_color = lerp(quantized, edge_color, edge * edge_intensity);
    
    return float4(final_color, color.a);
}
