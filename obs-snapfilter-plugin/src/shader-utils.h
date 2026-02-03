#ifndef SHADER_UTILS_H
#define SHADER_UTILS_H

#include <string>
#include <vector>

// Shader utility functions
namespace ShaderUtils {
    
    // Convert GLSL to OBS HLSL format
    std::string glsl_to_obs_hlsl(const std::string &glsl_code);
    
    // Validate shader syntax
    bool validate_shader(const std::string &shader_code, std::string &error_msg);
    
    // Extract uniforms from shader
    std::vector<std::pair<std::string, std::string>> extract_uniforms(const std::string &shader_code);
    
    // Generate OBS effect wrapper
    std::string generate_effect_wrapper(const std::string &pixel_shader);
    
    // Load shader from file
    std::string load_shader_file(const std::string &path);
    
}

#endif // SHADER_UTILS_H
