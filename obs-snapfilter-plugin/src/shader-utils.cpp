#include "shader-utils.h"
#include <sstream>
#include <regex>
#include <fstream>
#include <obs-module.h>

namespace ShaderUtils {

std::string glsl_to_obs_hlsl(const std::string &glsl_code)
{
    std::string hlsl = glsl_code;
    
    // Replace GLSL types with HLSL
    struct TypeMapping {
        const char *glsl;
        const char *hlsl;
    };
    
    static const TypeMapping mappings[] = {
        {"vec2", "float2"},
        {"vec3", "float3"},
        {"vec4", "float4"},
        {"mat2", "float2x2"},
        {"mat3", "float3x3"},
        {"mat4", "float4x4"},
        {"sampler2D", "texture2d"},
        {"texture2D", "image.Sample"},
        {"gl_FragCoord", "uv * uv_size"},
        {"gl_FragColor", "output_color"},
        {"mix", "lerp"},
        {"fract", "frac"},
    };
    
    for (const auto &mapping : mappings) {
        size_t pos = 0;
        while ((pos = hlsl.find(mapping.glsl, pos)) != std::string::npos) {
            hlsl.replace(pos, strlen(mapping.glsl), mapping.hlsl);
            pos += strlen(mapping.hlsl);
        }
    }
    
    // Replace in/out with HLSL semantics
    hlsl = std::regex_replace(hlsl, std::regex("\\bin\\s+"), "in ");
    hlsl = std::regex_replace(hlsl, std::regex("\\bout\\s+"), "out ");
    
    return hlsl;
}

bool validate_shader(const std::string &shader_code, std::string &error_msg)
{
    // Basic validation - check for required elements
    if (shader_code.find("mainImage") == std::string::npos &&
        shader_code.find("main") == std::string::npos) {
        error_msg = "Shader must contain mainImage() or main() function";
        return false;
    }
    
    if (shader_code.find("return") == std::string::npos) {
        error_msg = "Shader must have a return statement";
        return false;
    }
    
    // Check for balanced braces
    int brace_count = 0;
    for (char c : shader_code) {
        if (c == '{') brace_count++;
        if (c == '}') brace_count--;
        if (brace_count < 0) {
            error_msg = "Unbalanced braces in shader";
            return false;
        }
    }
    
    if (brace_count != 0) {
        error_msg = "Unbalanced braces in shader";
        return false;
    }
    
    return true;
}

std::vector<std::pair<std::string, std::string>> extract_uniforms(const std::string &shader_code)
{
    std::vector<std::pair<std::string, std::string>> uniforms;
    
    // Regex to find uniform declarations
    std::regex uniform_regex(R"(uniform\s+(\w+)\s+(\w+))");
    std::smatch match;
    
    std::string::const_iterator search_start(shader_code.cbegin());
    while (std::regex_search(search_start, shader_code.cend(), match, uniform_regex)) {
        std::string type = match[1].str();
        std::string name = match[2].str();
        uniforms.emplace_back(type, name);
        search_start = match.suffix().first;
    }
    
    return uniforms;
}

std::string generate_effect_wrapper(const std::string &pixel_shader)
{
    std::ostringstream wrapper;
    
    wrapper << R"(
uniform float4x4 ViewProj;
uniform texture2d image;
uniform float2 uv_scale;
uniform float2 uv_offset;
uniform float2 uv_size;
uniform float elapsed_time;

// Face tracking uniforms
uniform bool face_detected;
uniform float2 face_center;
uniform float2 face_size;
uniform float face_rotation;

sampler_state textureSampler {
    Filter = Linear;
    AddressU = Clamp;
    AddressV = Clamp;
};

struct VertData {
    float4 pos : POSITION;
    float2 uv : TEXCOORD0;
};

VertData VSDefault(VertData v_in)
{
    VertData vert_out;
    vert_out.pos = mul(float4(v_in.pos.xyz, 1.0), ViewProj);
    vert_out.uv = v_in.uv * uv_scale + uv_offset;
    return vert_out;
}

)";
    
    wrapper << pixel_shader;
    
    wrapper << R"(

technique Draw
{
    pass
    {
        vertex_shader = VSDefault(v_in);
        pixel_shader = mainImage(v_in);
    }
}
)";
    
    return wrapper.str();
}

std::string load_shader_file(const std::string &path)
{
    std::ifstream file(path);
    if (!file.is_open()) {
        blog(LOG_ERROR, "Failed to open shader file: %s", path.c_str());
        return "";
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

} // namespace ShaderUtils
