cmake_minimum_required(VERSION 3.16)
project(obs-snapfilter VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Require OBS 30+ for updated graphics API
set(OBS_MIN_VERSION "30.0.0")

# Find packages using pkg-config
find_package(PkgConfig REQUIRED)
find_package(Threads REQUIRED)
find_package(OpenCV REQUIRED)

# Find OBS - try pkg-config first, fall back to manual paths
pkg_check_modules(LIBOBS libobs)

if(NOT LIBOBS_FOUND)
    # Manual OBS setup for macOS/systems without pkg-config
    if(DEFINED OBS_SOURCE_DIR)
        message(STATUS "Using OBS source from: ${OBS_SOURCE_DIR}")
        set(LIBOBS_INCLUDE_DIRS "${OBS_SOURCE_DIR}/libobs")
        # On macOS, link against framework in /Applications/OBS.app
        if(APPLE)
            set(LIBOBS_FRAMEWORK "/Applications/OBS.app/Contents/Frameworks/libobs.framework")
            if(EXISTS ${LIBOBS_FRAMEWORK})
                set(LIBOBS_LIBRARIES "${LIBOBS_FRAMEWORK}/libobs")
            else()
                message(WARNING "libobs.framework not found - plugin will compile but not link")
                set(LIBOBS_LIBRARIES "")
            endif()
        endif()
        set(LIBOBS_FOUND TRUE)
        set(LIBOBS_VERSION "32.0.0")  # Assume OBS 32+ when using source
    else()
        message(FATAL_ERROR "libobs not found via pkg-config. Set -DOBS_SOURCE_DIR=/path/to/obs-studio")
    endif()
endif()

# Verify OBS version (skip if manually configured)
if(LIBOBS_VERSION AND LIBOBS_VERSION VERSION_LESS ${OBS_MIN_VERSION})
    message(FATAL_ERROR "OBS Studio ${OBS_MIN_VERSION} or higher required. Found: ${LIBOBS_VERSION}")
endif()

# Find jsoncpp
pkg_check_modules(JSONCPP REQUIRED jsoncpp)

# MediaPipe setup (optional but recommended)
if(DEFINED MEDIAPIPE_DIR)
    include_directories(${MEDIAPIPE_DIR})
    add_definitions(-DUSE_MEDIAPIPE)
endif()

# Plugin header
set(obs-snapfilter_HEADERS
    include/obs-snapfilter.h
    include/version.h
    src/snap-filter.h
    src/face-tracker.h
    src/shader-utils.h
    src/lens-loader.h
)

# Plugin sources
set(obs-snapfilter_SOURCES
    src/main.cpp
    src/snap-filter.cpp
    src/face-tracker.cpp
    src/shader-utils.cpp
    src/lens-loader.cpp
)

# Create library
add_library(obs-snapfilter MODULE
    ${obs-snapfilter_SOURCES}
    ${obs-snapfilter_HEADERS}
)

# Find simde (required by OBS for SIMD support)
find_path(SIMDE_INCLUDE_DIR simde/x86/sse2.h
    HINTS /opt/homebrew/opt/simde/include /usr/local/include
)

# Include directories
target_include_directories(obs-snapfilter PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${LIBOBS_INCLUDE_DIRS}
    ${OpenCV_INCLUDE_DIRS}
    ${JSONCPP_INCLUDE_DIRS}
    ${SIMDE_INCLUDE_DIR}
)

# Link libraries (use target_link_directories for jsoncpp)
target_link_directories(obs-snapfilter PRIVATE ${JSONCPP_LIBRARY_DIRS})
target_link_libraries(obs-snapfilter PRIVATE
    ${LIBOBS_LIBRARIES}
    ${OpenCV_LIBS}
    ${JSONCPP_LIBRARIES}
    Threads::Threads
)

# Platform-specific settings
if(WIN32)
    target_link_libraries(obs-snapfilter PRIVATE
        opengl32
        glu32
    )
    set_target_properties(obs-snapfilter PROPERTIES
        PREFIX ""
    )
elseif(APPLE)
    set_target_properties(obs-snapfilter PROPERTIES
        PREFIX ""
        SUFFIX ".so"
    )
else()
    set_target_properties(obs-snapfilter PROPERTIES
        PREFIX ""
    )
endif()

# Copy data files
set(obs-snapfilter_DATA
    data/locale/en-US.ini
    data/shaders/default.shader
    data/shaders/face-mask.shader
    data/shaders/beauty-filter.shader
    data/shaders/cartoon.shader
    data/shaders/lut.shader
    data/presets/default.json
)

# Install
install(TARGETS obs-snapfilter
    LIBRARY DESTINATION obs-plugins/64bit
    RUNTIME DESTINATION obs-plugins/64bit
)

install(FILES ${obs-snapfilter_DATA}
    DESTINATION data/obs-plugins/obs-snapfilter
)

# Testing
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
