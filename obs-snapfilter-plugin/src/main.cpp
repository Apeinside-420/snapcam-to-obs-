#include "obs-snapfilter.h"
#include "snap-filter.h"
#include <obs-module.h>

// OBS module declaration - must be in exactly one source file
OBS_DECLARE_MODULE()
OBS_MODULE_USE_DEFAULT_LOCALE("obs-snapfilter", "en-US")

bool obs_module_load(void)
{
    blog(LOG_INFO, "Snap Camera Filter plugin loaded (version %s)", OBS_SNAPFILTER_VERSION);
    
    // Register the filter
    struct obs_source_info snap_filter_info = {};
    snap_filter_info.id = OBS_SNAPFILTER_ID;
    snap_filter_info.type = OBS_SOURCE_TYPE_FILTER;
    snap_filter_info.output_flags = OBS_SOURCE_VIDEO;
    snap_filter_info.get_name = snapfilter_get_name;
    snap_filter_info.create = snapfilter_create;
    snap_filter_info.destroy = snapfilter_destroy;
    snap_filter_info.update = snapfilter_update;
    snap_filter_info.get_properties = snapfilter_properties;
    snap_filter_info.get_defaults = snapfilter_defaults;
    snap_filter_info.video_render = snapfilter_render;
    snap_filter_info.video_tick = snapfilter_tick;
    snap_filter_info.filter_remove = snapfilter_filter_remove;
    
    obs_register_source(&snap_filter_info);
    
    return true;
}

void obs_module_unload(void)
{
    blog(LOG_INFO, "Snap Camera Filter plugin unloaded");
}

const char *obs_module_name(void)
{
    return "Snap Camera Filter for OBS";
}

const char *obs_module_description(void)
{
    return "Provides Snap Camera-style face tracking and filters for OBS Studio";
}
