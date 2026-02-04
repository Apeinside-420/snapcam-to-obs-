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

# Find OBS using pkg-config
pkg_check_modules(LIBOBS REQUIRED libobs)

# Verify OBS version
if(LIBOBS_VERSION VERSION_LESS ${OBS_MIN_VERSION})
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

# Include directories
target_include_directories(obs-snapfilter PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${LIBOBS_INCLUDE_DIRS}
    ${OpenCV_INCLUDE_DIRS}
    ${JSONCPP_INCLUDE_DIRS}
)

# Link libraries
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
