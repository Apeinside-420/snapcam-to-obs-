#include "snap-filter.h"
#include "shader-utils.h"
#include <graphics/graphics.h>
#include <graphics/matrix4.h>

const char *snapfilter_get_name(void *unused)
{
    return OBS_SNAPFILTER_NAME;
}

void *snapfilter_create(obs_data_t *settings, obs_source_t *source)
{
    snapfilter_data *filter = new snapfilter_data();
    filter->context = source;
    filter->tracking_enabled = true;
    filter->face_detected = false;
    filter->intensity = 0.5f;
    filter->use_face_mask = true;
    filter->smooth_factor = 0.3f;
    filter->should_exit = false;
    filter->start_time = obs_get_video_frame_time();
    filter->elapsed_time = 0.0f;
    
    // Initialize face tracker
    filter->face_tracker = std::make_unique<FaceTracker>();
    if (!filter->face_tracker->initialize()) {
        blog(LOG_WARNING, "Failed to initialize face tracker");
    }
    
    // Initialize lens loader
    filter->lens_loader = std::make_unique<LensLoader>();
    
    // Initialize shader
    char *shader_path = obs_module_file("data/shaders/default.shader");
    if (shader_path) {
        load_shader(filter, shader_path);
        bfree(shader_path);
    }
    
    // Initialize face data (use vec2_set for OBS 30+ structs)
    vec2_set(&filter->face_center, 0.5f, 0.5f);
    vec2_set(&filter->face_size, 0.0f, 0.0f);
    filter->face_rotation = 0.0f;
    filter->face_confidence = 0.0f;

    // Initialize tint color (use vec4_set for OBS 30+ structs)
    vec4_set(&filter->tint_color, 1.0f, 1.0f, 1.0f, 1.0f);
    
    // Start tracking thread
    filter->tracking_thread = std::thread([filter]() {
        while (!filter->should_exit) {
            if (filter->tracking_enabled && filter->face_tracker) {
                update_face_tracking(filter);
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(33)); // ~30fps
        }
    });
    
    snapfilter_update(filter, settings);
    
    return filter;
}

void snapfilter_destroy(void *data)
{
    snapfilter_data *filter = static_cast<snapfilter_data*>(data);
    
    // Signal thread to exit
    filter->should_exit = true;
    if (filter->tracking_thread.joinable()) {
        filter->tracking_thread.join();
    }
    
    // Cleanup shaders
    if (filter->effect) {
        obs_enter_graphics();
        gs_effect_destroy(filter->effect);
        obs_leave_graphics();
    }
    
    delete filter;
}

void snapfilter_update(void *data, obs_data_t *settings)
{
    snapfilter_data *filter = static_cast<snapfilter_data*>(data);
    
    std::lock_guard<std::mutex> lock(filter->data_mutex);
    
    filter->intensity = (float)obs_data_get_double(settings, "intensity");
    filter->use_face_mask = obs_data_get_bool(settings, "use_face_mask");
    filter->tracking_enabled = obs_data_get_bool(settings, "tracking_enabled");
    filter->smooth_factor = (float)obs_data_get_double(settings, "smooth_factor");
    
    // Load color (extract ARGB components into vec4)
    uint32_t color = obs_data_get_int(settings, "tint_color");
    vec4_set(&filter->tint_color,
        ((color >> 16) & 0xFF) / 255.0f,  // R
        ((color >> 8) & 0xFF) / 255.0f,   // G
        (color & 0xFF) / 255.0f,          // B
        ((color >> 24) & 0xFF) / 255.0f); // A
    
    // Load lens file if specified
    const char *lens_path = obs_data_get_string(settings, "lens_file");
    if (lens_path && strlen(lens_path) > 0 && 
        filter->current_lens_path != lens_path) {
        filter->current_lens_path = lens_path;
        filter->lens_loader->load_lens(lens_path, filter);
    }
}

obs_properties_t *snapfilter_properties(void *data)
{
    snapfilter_data *filter = static_cast<snapfilter_data*>(data);
    
    obs_properties_t *props = obs_properties_create();
    
    // Tracking toggle
    obs_properties_add_bool(props, "tracking_enabled", 
                            obs_module_text("EnableFaceTracking"));
    
    // Lens file selector
    obs_properties_add_path(props, "lens_file", 
                           obs_module_text("LensFile"),
                           OBS_PATH_FILE,
                           "Lens files (*.lns *.zip);;All files (*.*)",
                           nullptr);
    
    // Filter intensity
    obs_properties_add_float_slider(props, "intensity",
                                    obs_module_text("FilterIntensity"),
                                    0.0, 1.0, 0.01);
    
    // Face mask toggle
    obs_properties_add_bool(props, "use_face_mask",
                           obs_module_text("UseFaceMask"));
    
    // Tint color
    obs_properties_add_color(props, "tint_color",
                            obs_module_text("TintColor"));
    
    // Smooth factor
    obs_properties_add_float_slider(props, "smooth_factor",
                                    obs_module_text("TrackingSmoothness"),
                                    0.0, 1.0, 0.01);
    
    // Reload button
    obs_properties_add_button(props, "reload_lens",
                             obs_module_text("ReloadLens"),
                             [](obs_properties_t *props, obs_property_t *property, void *data) {
                                 snapfilter_data *filter = static_cast<snapfilter_data*>(data);
                                 if (!filter->current_lens_path.empty()) {
                                     filter->lens_loader->load_lens(filter->current_lens_path.c_str(), filter);
                                 }
                                 return true;
                             });
    
    return props;
}

void snapfilter_defaults(obs_data_t *settings)
{
    obs_data_set_default_bool(settings, "tracking_enabled", true);
    obs_data_set_default_double(settings, "intensity", 0.5);
    obs_data_set_default_bool(settings, "use_face_mask", true);
    obs_data_set_default_int(settings, "tint_color", 0xFFFFFFFF);
    obs_data_set_default_double(settings, "smooth_factor", 0.3);
}

void snapfilter_tick(void *data, float seconds)
{
    snapfilter_data *filter = static_cast<snapfilter_data*>(data);
    
    uint64_t current_time = obs_get_video_frame_time();
    filter->elapsed_time = (current_time - filter->start_time) / 1000000000.0f;
}

void snapfilter_render(void *data, gs_effect_t *effect)
{
    snapfilter_data *filter = static_cast<snapfilter_data*>(data);
    
    if (!filter->effect) {
        obs_source_skip_video_filter(filter->context);
        return;
    }
    
    obs_source_t *target = obs_filter_get_target(filter->context);
    if (!target) {
        obs_source_skip_video_filter(filter->context);
        return;
    }
    
    render_filter(filter, target);
}

void snapfilter_filter_remove(void *data, obs_source_t *parent)
{
    UNUSED_PARAMETER(data);
    UNUSED_PARAMETER(parent);
}

void load_shader(snapfilter_data *filter, const char *shader_path)
{
    obs_enter_graphics();
    
    if (filter->effect) {
        gs_effect_destroy(filter->effect);
        filter->effect = nullptr;
    }
    
    char *error = nullptr;
    filter->effect = gs_effect_create_from_file(shader_path, &error);
    
    if (error) {
        blog(LOG_ERROR, "Error loading shader: %s", error);
        bfree(error);
    }
    
    if (filter->effect) {
        filter->param_image = gs_effect_get_param_by_name(filter->effect, "image");
        filter->param_face_center = gs_effect_get_param_by_name(filter->effect, "face_center");
        filter->param_face_size = gs_effect_get_param_by_name(filter->effect, "face_size");
        filter->param_face_rotation = gs_effect_get_param_by_name(filter->effect, "face_rotation");
        filter->param_face_detected = gs_effect_get_param_by_name(filter->effect, "face_detected");
        filter->param_elapsed_time = gs_effect_get_param_by_name(filter->effect, "elapsed_time");
        filter->param_intensity = gs_effect_get_param_by_name(filter->effect, "intensity");
        filter->param_tint_color = gs_effect_get_param_by_name(filter->effect, "tint_color");
    }
    
    obs_leave_graphics();
}

void update_face_tracking(snapfilter_data *filter)
{
    if (!filter->face_tracker) return;
    
    // Get the source frame for face detection
    obs_source_t *target = obs_filter_get_target(filter->context);
    if (!target) return;
    
    // Process frame through face tracker
    FaceData face_data = filter->face_tracker->process_frame(target);
    
    std::lock_guard<std::mutex> lock(filter->data_mutex);
    
    // Smooth the face data (accessing struct vec2 members with .x and .y)
    float alpha = filter->smooth_factor;
    filter->face_center.x = filter->face_center.x * (1.0f - alpha) + face_data.center_x * alpha;
    filter->face_center.y = filter->face_center.y * (1.0f - alpha) + face_data.center_y * alpha;
    filter->face_size.x = filter->face_size.x * (1.0f - alpha) + face_data.width * alpha;
    filter->face_size.y = filter->face_size.y * (1.0f - alpha) + face_data.height * alpha;
    filter->face_rotation = filter->face_rotation * (1.0f - alpha) + face_data.rotation * alpha;
    filter->face_confidence = face_data.confidence;
    filter->face_detected = face_data.confidence > 0.5f;
}

void render_filter(snapfilter_data *filter, obs_source_t *target)
{
    uint32_t width = obs_source_get_base_width(target);
    uint32_t height = obs_source_get_base_height(target);
    
    gs_texture_t *tex = gs_texture_create(width, height, GS_RGBA, 1, nullptr, 0);
    if (!tex) {
        obs_source_skip_video_filter(filter->context);
        return;
    }
    
    // Render source to texture
    gs_texture_render_start(tex);
    obs_source_video_render(target);
    gs_texture_render_end(tex);
    
    // Set shader parameters
    if (filter->param_image) {
        gs_effect_set_texture(filter->param_image, tex);
    }
    
    {
        std::lock_guard<std::mutex> lock(filter->data_mutex);
        
        if (filter->param_face_center) {
            gs_effect_set_vec2(filter->param_face_center, &filter->face_center);
        }
        if (filter->param_face_size) {
            gs_effect_set_vec2(filter->param_face_size, &filter->face_size);
        }
        if (filter->param_face_rotation) {
            gs_effect_set_float(filter->param_face_rotation, filter->face_rotation);
        }
        if (filter->param_face_detected) {
            gs_effect_set_bool(filter->param_face_detected, filter->face_detected);
        }
        if (filter->param_elapsed_time) {
            gs_effect_set_float(filter->param_elapsed_time, filter->elapsed_time);
        }
        if (filter->param_intensity) {
            gs_effect_set_float(filter->param_intensity, filter->intensity);
        }
        if (filter->param_tint_color) {
            gs_effect_set_vec4(filter->param_tint_color, &filter->tint_color);
        }
    }
    
    // Render with shader
    while (gs_effect_loop(filter->effect, "Draw")) {
        gs_draw_sprite(tex, 0, width, height);
    }
    
    gs_texture_destroy(tex);
}
