#ifndef LENS_LOADER_H
#define LENS_LOADER_H

#include <string>
#include <vector>
#include <memory>
#include <json/json.h>

struct LensData {
    std::string name;
    std::string description;
    std::string shader_path;
    std::vector<std::string> texture_paths;
    bool face_tracking;
    bool has_3d;
    Json::Value parameters;
};

class LensLoader {
public:
    LensLoader();
    ~LensLoader();
    
    // Load a converted lens from path
    bool load_lens(const std::string &lens_path, void *filter_data);
    
    // Get lens info
    LensData get_lens_data() const { return current_lens; }
    
    // Check if lens is loaded
    bool is_loaded() const { return !current_lens.shader_path.empty(); }
    
private:
    LensData current_lens;
    
    bool parse_lens_info(const std::string &info_path);
    bool load_shader_file(const std::string &shader_path);
    bool load_textures(const std::vector<std::string> &texture_paths);
};

#endif // LENS_LOADER_H
