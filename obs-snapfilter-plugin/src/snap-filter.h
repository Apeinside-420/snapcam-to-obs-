#ifndef SNAP_FILTER_H
#define SNAP_FILTER_H

#include <obs-module.h>
#include <opencv2/opencv.hpp>
#include <memory>
#include <string>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>
#include "face-tracker.h"
#include "lens-loader.h"

struct snapfilter_data {
    obs_source_t *context;
    
    // Face tracking
    std::unique_ptr<FaceTracker> face_tracker;
    std::atomic<bool> tracking_enabled;
    std::atomic<bool> face_detected;
    
    // Lens data
    std::unique_ptr<LensLoader> lens_loader;
    std::string current_lens_path;
    
    // Shader resources
    gs_effect_t *effect;
    gs_eparam_t *param_image;
    gs_eparam_t *param_face_center;
    gs_eparam_t *param_face_size;
    gs_eparam_t *param_face_rotation;
    gs_eparam_t *param_face_detected;
    gs_eparam_t *param_elapsed_time;
    gs_eparam_t *param_intensity;
    gs_eparam_t *param_tint_color;
    
    // Face tracking data
    float face_center[2];
    float face_size[2];
    float face_rotation;
    float face_confidence;
    
    // Filter parameters
    float intensity;
    float tint_color[4];
    bool use_face_mask;
    float smooth_factor;
    
    // Timing
    uint64_t start_time;
    float elapsed_time;
    
    // Threading
    std::mutex data_mutex;
    std::thread tracking_thread;
    std::atomic<bool> should_exit;
};

// OBS source interface
const char *snapfilter_get_name(void *unused);
void *snapfilter_create(obs_data_t *settings, obs_source_t *source);
void snapfilter_destroy(void *data);
void snapfilter_update(void *data, obs_data_t *settings);
obs_properties_t *snapfilter_properties(void *data);
void snapfilter_defaults(obs_data_t *settings);
void snapfilter_render(void *data, gs_effect_t *effect);
void snapfilter_tick(void *data, float seconds);
void snapfilter_filter_remove(void *data, obs_source_t *parent);

// Helper functions
void load_shader(snapfilter_data *filter, const char *shader_path);
void update_face_tracking(snapfilter_data *filter);
void render_filter(snapfilter_data *filter, obs_source_t *target);

#endif // SNAP_FILTER_H
