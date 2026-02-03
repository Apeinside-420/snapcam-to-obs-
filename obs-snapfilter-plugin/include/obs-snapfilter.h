#ifndef OBS_SNAPFILTER_H
#define OBS_SNAPFILTER_H

#ifdef __cplusplus
extern "C" {
#endif

#include <obs-module.h>

#define OBS_SNAPFILTER_ID "obs_snapfilter"
#define OBS_SNAPFILTER_NAME "Snap Camera Filter"
#define OBS_SNAPFILTER_VERSION "1.0.0"

OBS_DECLARE_MODULE()
OBS_MODULE_USE_DEFAULT_LOCALE("obs-snapfilter", "en-US")

bool obs_module_load(void);
void obs_module_unload(void);
const char *obs_module_name(void);
const char *obs_module_description(void);

#ifdef __cplusplus
}
#endif

#endif // OBS_SNAPFILTER_H
