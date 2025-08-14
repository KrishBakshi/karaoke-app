# Makefile for Autotune Karaoke Application
# Alternative to CMake build system

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2 -I.
LDFLAGS = -lportaudio -lsndfile -laubio -lSDL2

# Target executables
TARGET = autotune-karaoke
DEVICE_LIST = device_list

# Source files
SOURCES = karaoke.cpp simple_noise_suppression.cpp
DEVICE_SOURCES = device_list.cpp

# Object files
OBJECTS = $(SOURCES:.cpp=.o)

# Default target
all: $(TARGET) $(DEVICE_LIST)

# Build the main executable
$(TARGET): $(OBJECTS)
	$(CXX) $(OBJECTS) -o $(TARGET) $(LDFLAGS)
	@echo "✅ Built $(TARGET) successfully!"

# Build the device list utility
$(DEVICE_LIST): $(DEVICE_SOURCES)
	$(CXX) $(CXXFLAGS) $(DEVICE_SOURCES) -o $(DEVICE_LIST) -lportaudio
	@echo "✅ Built $(DEVICE_LIST) successfully!"

# Compile source files
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build files
clean:
	rm -f $(OBJECTS) $(TARGET) $(DEVICE_LIST)
	@echo "🧹 Cleaned build files"

# Install dependencies (Ubuntu/Debian)
install-deps:
	@echo "📦 Installing dependencies..."
	sudo apt-get update
	sudo apt-get install -y \
		libportaudio2 \
		libsndfile1-dev \
		libaubio-dev \
		libsdl2-dev \
		build-essential \
		cmake

# Install dependencies (Arch Linux)
install-deps-arch:
	@echo "📦 Installing dependencies (Arch)..."
	sudo pacman -S \
		portaudio \
		libsndfile \
		aubio \
		sdl2 \
		base-devel \
		cmake

# Install dependencies (macOS)
install-deps-macos:
	@echo "📦 Installing dependencies (macOS)..."
	brew install \
		portaudio \
		libsndfile \
		aubio \
		sdl2 \
		cmake

# Run the application
run: $(TARGET)
	@echo "🎵 Running autotune karaoke..."
	./$(TARGET) blinding_lights

# Help
help:
	@echo "🎤 Autotune Karaoke Build System"
	@echo "================================"
	@echo "make all          - Build the application and device list"
	@echo "make clean        - Clean build files"
	@echo "make install-deps - Install dependencies (Ubuntu/Debian)"
	@echo "make install-deps-arch - Install dependencies (Arch Linux)"
	@echo "make install-deps-macos - Install dependencies (macOS)"
	@echo "make run          - Build and run the application"
	@echo "make devices      - List available audio devices"
	@echo "make help         - Show this help message"

# List audio devices
devices: $(DEVICE_LIST)
	@echo "🔍 Listing available audio devices..."
	./$(DEVICE_LIST)

.PHONY: all clean install-deps install-deps-arch install-deps-macos run help devices
