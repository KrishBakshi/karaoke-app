cmake_minimum_required(VERSION 3.10)
project(AutotuneKaraoke VERSION 1.0.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(PkgConfig REQUIRED)

# Find PortAudio
find_library(PORTAUDIO_LIBRARY NAMES portaudio)
find_path(PORTAUDIO_INCLUDE_DIR NAMES portaudio.h)

# Find libsndfile
find_library(SNDFILE_LIBRARY NAMES sndfile)
find_path(SNDFILE_INCLUDE_DIR NAMES sndfile.h)

# Find Aubio
find_library(AUBIO_LIBRARY NAMES aubio)
find_path(AUBIO_INCLUDE_DIR NAMES aubio/aubio.h)

# Find SDL2
find_package(SDL2 REQUIRED)

# Check if all required libraries are found
if(NOT PORTAUDIO_LIBRARY OR NOT PORTAUDIO_INCLUDE_DIR)
    message(FATAL_ERROR "PortAudio not found!")
endif()

if(NOT SNDFILE_LIBRARY OR NOT SNDFILE_INCLUDE_DIR)
    message(FATAL_ERROR "libsndfile not found!")
endif()

if(NOT AUBIO_LIBRARY OR NOT AUBIO_INCLUDE_DIR)
    message(FATAL_ERROR "Aubio not found!")
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${PORTAUDIO_INCLUDE_DIR})
include_directories(${SNDFILE_INCLUDE_DIR})
include_directories(${AUBIO_INCLUDE_DIR})

# Create executable
add_executable(autotune-karaoke
    karaoke.cpp
    simple_noise_suppression.cpp
)

# Link libraries
target_link_libraries(autotune-karaoke
    ${PORTAUDIO_LIBRARY}
    ${SNDFILE_LIBRARY}
    ${AUBIO_LIBRARY}
    SDL2::SDL2
)

# Set compiler flags
target_compile_options(autotune-karaoke PRIVATE
    -Wall
    -Wextra
    -O2
)

# Install target
install(TARGETS autotune-karaoke
    RUNTIME DESTINATION bin
)

# Copy data files
install(FILES
    melody_map.h
    DESTINATION include
)

# Print configuration info
message(STATUS "PortAudio: ${PORTAUDIO_LIBRARY}")
message(STATUS "libsndfile: ${SNDFILE_LIBRARY}")
message(STATUS "Aubio: ${AUBIO_LIBRARY}")
message(STATUS "SDL2: ${SDL2_LIBRARIES}")
