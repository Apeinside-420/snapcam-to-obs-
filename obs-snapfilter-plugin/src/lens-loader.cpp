#include "lens-loader.h"
#include "snap-filter.h"
#include <fstream>
#include <obs-module.h>

LensLoader::LensLoader()
{
}

LensLoader::~LensLoader()
{
}

bool LensLoader::load_lens(const std::string &lens_path, void *filter_data)
{
    snapfilter_data *filter = static_cast<snapfilter_data*>(filter_data);
    
    // Check if this is a directory (converted lens) or a file
    std::string info_path = lens_path + "/obs_assets/lens_info.json";
    std::string shader_path = lens_path + "/obs_assets/snap_filter.shader";
    
    // Parse lens info
    if (!parse_lens_info(info_path)) {
        blog(LOG_WARNING, "Failed to parse lens info: %s", info_path.c_str());
        return false;
    }
    
    // Load shader
    if (!current_lens.shader_path.empty()) {
        load_shader(filter, current_lens.shader_path.c_str());
    }
    
    // Load textures if any
    if (!current_lens.texture_paths.empty()) {
        load_textures(current_lens.texture_paths);
    }
    
    blog(LOG_INFO, "Loaded lens: %s", current_lens.name.c_str());
    return true;
}

bool LensLoader::parse_lens_info(const std::string &info_path)
{
    std::ifstream file(info_path);
    if (!file.is_open()) {
        blog(LOG_ERROR, "Cannot open lens info: %s", info_path.c_str());
        return false;
    }
    
    Json::Value root;
    Json::CharReaderBuilder builder;
    std::string errors;
    
    if (!Json::parseFromStream(builder, file, &root, &errors)) {
        blog(LOG_ERROR, "Failed to parse lens JSON: %s", errors.c_str());
        return false;
    }
    
    current_lens.name = root.get("name", "Unknown Lens").asString();
    current_lens.description = root.get("description", "").asString();
    current_lens.face_tracking = root.get("face_tracking", false).asBool();
    current_lens.has_3d = root.get("uses_3d", false).asBool();
    
    // Get shader path
    const Json::Value &files = root["files"];
    if (files.isObject()) {
        current_lens.shader_path = files.get("main_shader", "").asString();
        
        // Get texture paths
        const Json::Value &textures = files["textures"];
        if (textures.isArray()) {
            for (const auto &tex : textures) {
                current_lens.texture_paths.push_back(tex.asString());
            }
        }
    }
    
    // Get parameters
    if (root.isMember("parameters")) {
        current_lens.parameters = root["parameters"];
    }
    
    return true;
}

bool LensLoader::load_shader_file(const std::string &shader_path)
{
    // Shader loading is handled by the filter
    UNUSED_PARAMETER(shader_path);
    return true;
}

bool LensLoader::load_textures(const std::vector<std::string> &texture_paths)
{
    // Texture loading implementation
    UNUSED_PARAMETER(texture_paths);
    return true;
}
