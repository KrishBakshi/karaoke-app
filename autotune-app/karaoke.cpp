#include <iostream>
#include <vector>
#include <cmath>
#include <chrono>
#include <thread>
#include <deque>
#include <fstream>
#include <ctime>
#include <portaudio.h>
#include <sndfile.h>
#include <aubio/aubio.h>
#include <SDL2/SDL.h>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include "simple_noise_suppression.h"

// Function declarations
std::vector<std::pair<float, float>> loadMelodyMap(const std::string& filename);
void saveRecording(const std::vector<float>& recording_frames, const std::string& filename);
std::string generateUniqueFilename(const std::string& song_name);

// Function to load melody map from file
std::vector<std::pair<float, float>> loadMelodyMap(const std::string& filename) {
    std::vector<std::pair<float, float>> melody_map;
    
    // Check file extension (compatible with older C++ versions)
    if (filename.length() >= 4 && filename.substr(filename.length() - 4) == ".npz") {
        // Load from numpy .npz file (Python format)
        std::cout << "🎼 Loading melody map from numpy file: " << filename << std::endl;
        // For now, we'll use a simple text format, but you can extend this
        std::cout << "⚠️  .npz files not yet supported, please convert to .txt format" << std::endl;
        return melody_map;
    } else if (filename.length() >= 4 && filename.substr(filename.length() - 4) == ".txt") {
        // Load from simple text file
        std::cout << "🎼 Loading melody map from text file: " << filename << std::endl;
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "❌ Could not open melody file: " << filename << std::endl;
            return melody_map;
        }
        
        std::string line;
        // Skip header lines (start with #)
        while (std::getline(file, line) && line[0] == '#') {
            continue;
        }
        
        // Read melody data: time,frequency format
        while (std::getline(file, line)) {
            if (line.empty()) continue;
            
            size_t comma_pos = line.find(',');
            if (comma_pos != std::string::npos) {
                float time = std::stof(line.substr(0, comma_pos));
                float freq = std::stof(line.substr(comma_pos + 1));
                melody_map.push_back({time, freq});
            }
        }
        
        file.close();
        std::cout << "✅ Loaded " << melody_map.size() << " melody points" << std::endl;
    } else {
        std::cerr << "❌ Unsupported file format. Use .txt or .npz files" << std::endl;
    }
    
    return melody_map;
}

// Function to generate unique filename
std::string generateUniqueFilename(const std::string& song_name) {
    // Create output directory if it doesn't exist
    std::filesystem::create_directories("output");
    
    // Get current timestamp
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()) % 1000;
    
    // Format: output/songname_YYYYMMDD_HHMMSS_mmm.wav
    std::stringstream ss;
    ss << "output/" << song_name << "_" 
       << std::put_time(std::localtime(&time_t), "%Y%m%d_%H%M%S")
       << "_" << std::setfill('0') << std::setw(3) << ms.count()
       << ".wav";
    
    return ss.str();
}

#define SAMPLE_RATE 48000
#define FRAMES_PER_BUFFER 256  // Smaller buffer for faster response
#define NUM_CHANNELS 1
#define PLOT_WIDTH 800
#define PLOT_HEIGHT 400
#define PLOT_HISTORY 200

struct AudioData {
    std::deque<float> pitch_history;
    std::deque<float> target_pitch_history;
    std::vector<std::pair<float, float>> melody_map;
    float current_time;
    std::vector<float> instrumental;
    size_t instrumental_pos;
    aubio_pitch_t* pitch_detector;
    float last_pitch;
    float last_confidence;
    std::deque<float> target_history;  // Added back target history
    std::deque<float> time_history;    // Added back time history
    std::vector<float> recording_frames; // For recording the mixed audio
    bool recording_enabled;
    SimpleNoiseSuppressor* noise_suppressor; // Added noise suppressor
    float autotune_strength;        // 0.0 = no effect, 1.0 = full autotune
    float pitch_shift_amount;       // -12.0 to +12.0 semitones
    float voice_volume;             // 0.0 to 2.0 multiplier
    float instrument_volume;        // 0.0 to 2.0 multiplier for instrumental
    bool enable_chorus;             // Enable chorus effect
    float chorus_depth;             // Chorus intensity
    bool enable_reverb;             // Enable reverb effect
    float reverb_wetness;
};

// Function to find default input and output devices
PaDeviceIndex findDefaultInputDevice() {
    PaDeviceIndex defaultDevice = Pa_GetDefaultInputDevice();
    if (defaultDevice != paNoDevice) {
        return defaultDevice;
    }
    
    // If no default, find any input device
    int numDevices = Pa_GetDeviceCount();
    for (int i = 0; i < numDevices; i++) {
        const PaDeviceInfo* deviceInfo = Pa_GetDeviceInfo(i);
        if (deviceInfo->maxInputChannels > 0) {
            // Prefer USB audio devices (like EarPods)
            std::string deviceName = deviceInfo->name;
            if (deviceName.find("USB") != std::string::npos || 
                deviceName.find("EarPods") != std::string::npos) {
                std::cout << "🎤 Using USB audio input device: " << deviceInfo->name << std::endl;
                return i;
            }
        }
    }
    
    // Fallback to any input device
    for (int i = 0; i < numDevices; i++) {
        const PaDeviceInfo* deviceInfo = Pa_GetDeviceInfo(i);
        if (deviceInfo->maxInputChannels > 0) {
            std::cout << "🎤 Using input device: " << deviceInfo->name << std::endl;
            return i;
        }
    }
    return paNoDevice;
}

PaDeviceIndex findDefaultOutputDevice() {
    PaDeviceIndex defaultDevice = Pa_GetDefaultOutputDevice();
    if (defaultDevice != paNoDevice) {
        return defaultDevice;
    }
    
    // If no default, find any output device
    int numDevices = Pa_GetDeviceCount();
    for (int i = 0; i < numDevices; i++) {
        const PaDeviceInfo* deviceInfo = Pa_GetDeviceInfo(i);
        if (deviceInfo->maxOutputChannels > 0) {
            // Prefer USB audio devices (like EarPods)
            std::string deviceName = deviceInfo->name;
            if (deviceName.find("USB") != std::string::npos || 
                deviceName.find("EarPods") != std::string::npos) {
                std::cout << "🎧 Using USB audio output device: " << deviceInfo->name << std::endl;
                return i;
            }
        }
    }
    
    // Fallback to any output device
    for (int i = 0; i < numDevices; i++) {
        const PaDeviceInfo* deviceInfo = Pa_GetDeviceInfo(i);
        if (deviceInfo->maxOutputChannels > 0) {
            std::cout << "🔊 Using output device: " << deviceInfo->name << std::endl;
            return i;
        }
    }
    return paNoDevice;
}

// Function to check for parameter updates from file
void checkParameterUpdates(AudioData* data) {
    static time_t last_check = 0;
    time_t current_time = time(nullptr);
    
    // Only check every 100ms to avoid excessive file I/O
    if (current_time - last_check < 0.1) {
        return;
    }
    last_check = current_time;
    
    std::ifstream param_file("voice_params.txt");
    if (param_file.is_open()) {
        std::string line;
        while (std::getline(param_file, line)) {
            if (line.find("voice_volume=") == 0) {
                float new_volume = std::stof(line.substr(13));
                if (new_volume >= 0.0f && new_volume <= 5.0f) {
                    data->voice_volume = new_volume;
                    std::cout << "🎤 Voice volume updated to: " << new_volume << std::endl;
                }
            } else if (line.find("autotune_strength=") == 0) {
                float new_strength = std::stof(line.substr(18));
                if (new_strength >= 0.0f && new_strength <= 2.0f) {
                    data->autotune_strength = new_strength;
                    std::cout << "🎵 Autotune strength updated to: " << new_strength << std::endl;
                }
            } else if (line.find("pitch_shift=") == 0) {
                float new_shift = std::stof(line.substr(12));
                if (new_shift >= -12.0f && new_shift <= 12.0f) {
                    data->pitch_shift_amount = new_shift;
                    std::cout << "🎼 Pitch shift updated to: " << new_shift << " semitones" << std::endl;
                }
            } else if (line.find("instrument_volume=") == 0) {
                float new_volume = std::stof(line.substr(18));
                if (new_volume >= 0.0f && new_volume <= 5.0f) {
                    data->instrument_volume = new_volume;
                    std::cout << "🎛️ Instrument volume updated to: " << new_volume << std::endl;
                }
            }
        }
        param_file.close();
    }
}

static int audioCallback(const void* inputBuffer, void* outputBuffer,
                        unsigned long framesPerBuffer,
                        const PaStreamCallbackTimeInfo* timeInfo,
                        PaStreamCallbackFlags statusFlags,
                        void* userData) {
    
    (void)framesPerBuffer; // Suppress unused parameter warning
    (void)timeInfo;        // Suppress unused parameter warning
    (void)statusFlags;     // Suppress unused parameter warning
    
    AudioData* data = (AudioData*)userData;
    float* in = (float*)inputBuffer;
    float* out = (float*)outputBuffer;
    
    // Safety check for null pointers
    if (!in || !out || !data) {
        return paAbort;
    }
    
    // Check for parameter updates
    checkParameterUpdates(data);
    
    // Get instrumental chunk
    std::vector<float> instrumental_chunk(FRAMES_PER_BUFFER, 0.0f);
    for (int i = 0; i < FRAMES_PER_BUFFER; i++) {
        if (data->instrumental_pos >= data->instrumental.size()) {
            data->instrumental_pos = 0;
        }
        if (!data->instrumental.empty()) {
            instrumental_chunk[i] = data->instrumental[data->instrumental_pos++];
        }
    }
    
    // Debug: Check if instrumental has non-zero values
    static int debug_counter = 0;
    if (debug_counter++ % 100 == 0) {  // Print every 100th callback
        float max_instrumental = 0.0f;
        float max_raw_instrumental = 0.0f;
        
        // Check the raw instrumental data
        if (!data->instrumental.empty()) {
            size_t start_pos = data->instrumental_pos;
            for (int i = 0; i < std::min(FRAMES_PER_BUFFER, (int)data->instrumental.size() - (int)start_pos); i++) {
                max_raw_instrumental = std::max(max_raw_instrumental, std::abs(data->instrumental[start_pos + i]));
            }
        }
        
        // Check the chunk data
        for (int i = 0; i < FRAMES_PER_BUFFER; i++) {
            max_instrumental = std::max(max_instrumental, std::abs(instrumental_chunk[i]));
        }
        
        std::cout << "🔍 Debug - Raw instrumental max: " << max_raw_instrumental 
                  << ", Chunk max: " << max_instrumental 
                  << ", Position: " << data->instrumental_pos 
                  << ", Total size: " << data->instrumental.size() << std::endl;
    }
    
    // Process input audio with higher sensitivity
    fvec_t* input_vec = new_fvec(FRAMES_PER_BUFFER);
    if (!input_vec) {
        return paAbort;
    }
    
    for (int i = 0; i < FRAMES_PER_BUFFER; i++) {
        input_vec->data[i] = in[i];
    }
    
    // Detect pitch with improved sensitivity
    fvec_t* pitch_output = new_fvec(1);
    if (!pitch_output) {
        del_fvec(input_vec);
        return paAbort;
    }
    
    aubio_pitch_do(data->pitch_detector, input_vec, pitch_output);
    float pitch = pitch_output->data[0];
    float confidence = aubio_pitch_get_confidence(data->pitch_detector);
    
    // Lower confidence threshold for faster detection
    if (confidence > 0.3f && pitch > 50.0f) {  // Lower threshold, higher minimum pitch
        data->last_pitch = pitch;
        data->last_confidence = confidence;
    }
    
    // Get target melody frequency
    float target_pitch = 0.0f;
    // More flexible lookup - find closest melody note within 0.5 seconds
    float best_time_diff = 0.5f;
    for (const auto& note : data->melody_map) {
        float time_diff = std::abs(note.first - data->current_time);
        if (time_diff < best_time_diff) {
            best_time_diff = time_diff;
            target_pitch = note.second;
        }
    }
    
    // Initialize processed audio buffer
    std::vector<float> processed_audio(FRAMES_PER_BUFFER);
    
    // Apply autotune with variable strength
    if (data->last_confidence > 0.5f && data->last_pitch > 0.0f && target_pitch > 0.0f) {
        float base_shift_ratio = target_pitch / data->last_pitch;
        
        // Apply autotune strength (0.0 = original pitch, 1.0 = full autotune)
        float shift_ratio = 1.0f + (base_shift_ratio - 1.0f) * data->autotune_strength;
        
        // Apply additional pitch shift
        float semitone_shift = pow(2.0f, data->pitch_shift_amount / 12.0f);
        shift_ratio *= semitone_shift;
        
        // Debug output for autotune and pitch shift
        static int effect_debug_counter = 0;
        if (effect_debug_counter++ % 1000 == 0) {  // Print every 1000th callback
            std::cout << "🎵 Effects applied - Autotune: " << data->autotune_strength 
                      << ", Pitch shift: " << data->pitch_shift_amount << " semitones" << std::endl;
        }
        
        // Process audio with new ratio
        for (int i = 0; i < FRAMES_PER_BUFFER; i++) {
            int shifted_idx = (int)(i * shift_ratio);
            if (shifted_idx < FRAMES_PER_BUFFER) {
                processed_audio[i] = in[shifted_idx];
            } else {
                processed_audio[i] = 0.0f;
            }
        }
    } else {
        // If no autotune, copy input directly
        static int no_effect_debug_counter = 0;
        if (no_effect_debug_counter++ % 1000 == 0) {  // Print every 1000th callback
            std::cout << "🔇 No effects - Autotune: " << data->autotune_strength 
                      << ", Pitch shift: " << data->pitch_shift_amount << " semitones" << std::endl;
        }
        
        for (int i = 0; i < FRAMES_PER_BUFFER; i++) {
            processed_audio[i] = in[i];
        }
    }
    
    // Apply noise suppression
    if (data->noise_suppressor) {
        data->noise_suppressor->processAudio(processed_audio.data(), processed_audio.data(), FRAMES_PER_BUFFER);
    }
    
    // Dynamic mixing based on voice and instrument volume settings
    static int volume_debug_counter = 0;
    if (volume_debug_counter++ % 1000 == 0) {  // Print every 1000th callback
        std::cout << "🔊 Audio mixing - Instrument vol: " << data->instrument_volume 
                  << ", Voice vol: " << data->voice_volume << std::endl;
    }
    
    for (int i = 0; i < FRAMES_PER_BUFFER; i++) {
        out[i] = data->instrument_volume * instrumental_chunk[i] + data->voice_volume * processed_audio[i];
        
        // Apply chorus effect if enabled
        if (data->enable_chorus) {
            // Simple chorus implementation
            float chorus_offset = sin(data->current_time * 2.0f * M_PI * 0.5f) * data->chorus_depth;
            int chorus_idx = (int)(i + chorus_offset) % FRAMES_PER_BUFFER;
            out[i] += 0.3f * processed_audio[chorus_idx];
            
            // Debug output for chorus (only once per buffer)
            if (i == 0) {
                static int chorus_debug_counter = 0;
                if (chorus_debug_counter++ % 1000 == 0) {  // Print every 1000th buffer
                    std::cout << "🎭 Chorus enabled - Depth: " << data->chorus_depth << std::endl;
                }
            }
        }
        
        // Clamp to prevent clipping
        if (out[i] > 1.0f) out[i] = 1.0f;
        if (out[i] < -1.0f) out[i] = -1.0f;
    }
    
    data->current_time += (float)FRAMES_PER_BUFFER / SAMPLE_RATE;
    
    // Update history for plotting
    data->pitch_history.push_back(data->last_pitch);
    data->target_history.push_back(target_pitch);
    data->time_history.push_back(data->current_time);
    
    if (data->pitch_history.size() > PLOT_HISTORY) {
        data->pitch_history.pop_front();
        data->target_history.pop_front();
        data->time_history.pop_front();
    }
    
    // Cleanup
    del_fvec(input_vec);
    del_fvec(pitch_output);
    
    return paContinue;
}

void drawPlot(SDL_Renderer* renderer, const AudioData& data) {
    // Clear screen
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255);
    SDL_RenderClear(renderer);
    
    // Draw grid
    SDL_SetRenderDrawColor(renderer, 50, 50, 50, 255);
    for (int i = 0; i <= 10; i++) {
        int x = (PLOT_WIDTH * i) / 10;
        SDL_RenderDrawLine(renderer, x, 0, x, PLOT_HEIGHT);
    }
    for (int i = 0; i <= 8; i++) {
        int y = (PLOT_HEIGHT * i) / 8;
        SDL_RenderDrawLine(renderer, 0, y, PLOT_WIDTH, y);
    }
    
    // Draw pitch history (green)
    if (data.pitch_history.size() > 1) {
        SDL_SetRenderDrawColor(renderer, 0, 255, 0, 255);
        for (size_t i = 1; i < data.pitch_history.size(); i++) {
            float pitch1 = data.pitch_history[i-1];
            float pitch2 = data.pitch_history[i];
            float time1 = data.time_history[i-1];
            float time2 = data.time_history[i];
            
            if (pitch1 > 0 && pitch2 > 0) {
                int x1 = (int)((time1 - data.time_history.front()) * 100) % PLOT_WIDTH;
                int x2 = (int)((time2 - data.time_history.front()) * 100) % PLOT_WIDTH;
                int y1 = PLOT_HEIGHT - (int)((pitch1 - 50) * PLOT_HEIGHT / 800);
                int y2 = PLOT_HEIGHT - (int)((pitch2 - 50) * PLOT_HEIGHT / 800);
                
                y1 = std::max(0, std::min(PLOT_HEIGHT-1, y1));
                y2 = std::max(0, std::min(PLOT_HEIGHT-1, y2));
                
                SDL_RenderDrawLine(renderer, x1, y1, x2, y2);
            }
        }
    }
    
    // Draw target melody (red)
    if (data.target_history.size() > 1) {
        SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255);
        for (size_t i = 1; i < data.target_history.size(); i++) {
            float target1 = data.target_history[i-1];
            float target2 = data.target_history[i];
            float time1 = data.time_history[i-1];
            float time2 = data.time_history[i];
            
            if (target1 > 0 && target2 > 0) {
                int x1 = (int)((time1 - data.time_history.front()) * 100) % PLOT_WIDTH;
                int x2 = (int)((time2 - data.time_history.front()) * 100) % PLOT_WIDTH;
                int y1 = PLOT_HEIGHT - (int)((target1 - 50) * PLOT_HEIGHT / 800);
                int y2 = PLOT_HEIGHT - (int)((target2 - 50) * PLOT_HEIGHT / 800);
                
                y1 = std::max(0, std::min(PLOT_HEIGHT-1, y1));
                y2 = std::max(0, std::min(PLOT_HEIGHT-1, y2));
                
                SDL_RenderDrawLine(renderer, x1, y1, x2, y2);
            }
        }
    }
    
    // Draw noise suppression info
    if (data.noise_suppressor) {
        float vad_prob = data.noise_suppressor->getVADProbability();
        float noise_level = data.noise_suppressor->getNoiseLevel();
        bool voice_active = data.noise_suppressor->isVoiceActive();
        
        // Draw VAD probability bar (top right)
        int bar_width = 100;
        int bar_height = 20;
        int bar_x = PLOT_WIDTH - bar_width - 10; // Adjusted to be relative to plot width
        int bar_y = 10;
        
        // Background
        SDL_SetRenderDrawColor(renderer, 50, 50, 50, 255);
        SDL_Rect bar_bg = {bar_x, bar_y, bar_width, bar_height};
        SDL_RenderFillRect(renderer, &bar_bg);
        
        // VAD level
        SDL_SetRenderDrawColor(renderer, 
            voice_active ? 0 : 255, 
            voice_active ? 255 : 0, 
            0, 255);
        int vad_width = (int)(bar_width * vad_prob);
        SDL_Rect vad_bar = {bar_x, bar_y, vad_width, bar_height};
        SDL_RenderFillRect(renderer, &vad_bar);
        
        // Border
        SDL_SetRenderDrawColor(renderer, 200, 200, 200, 255);
        SDL_RenderDrawRect(renderer, &bar_bg);
        
        // Text
        char info_text[128];
        snprintf(info_text, sizeof(info_text), "VAD: %.1f%% Noise: %.3f", 
                vad_prob * 100.0f, noise_level);
        
        // Simple text rendering (you might want to use SDL_ttf for better text)
        // For now, we'll just show the info in the console
        static int info_counter = 0;
        if (++info_counter % 100 == 0) { // Update every 100 frames
            std::cout << "🎤 VAD: " << (vad_prob * 100.0f) << "%, Noise: " << noise_level 
                      << ", Voice: " << (voice_active ? "ON" : "OFF") << std::endl;
        }
    }
    
    SDL_RenderPresent(renderer);
}



// Function to save recording as WAV file
void saveRecording(const std::vector<float>& recording_frames, const std::string& filename) {
    if (recording_frames.empty()) {
        std::cout << "❌ No recording data to save!" << std::endl;
        return;
    }
    
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::cout << "❌ Could not open file for writing: " << filename << std::endl;
        return;
    }
    
    // WAV header
    const int sampleRate = SAMPLE_RATE;
    const int numChannels = 1;
    const int bitsPerSample = 16;
    const int byteRate = sampleRate * numChannels * bitsPerSample / 8;
    const int blockAlign = numChannels * bitsPerSample / 8;
    const int dataSize = recording_frames.size() * sizeof(int16_t);
    const int fileSize = 36 + dataSize;
    
    // Write WAV header
    file.write("RIFF", 4);
    file.write(reinterpret_cast<const char*>(&fileSize), 4);
    file.write("WAVE", 4);
    file.write("fmt ", 4);
    
    int32_t fmtSize = 16;
    file.write(reinterpret_cast<const char*>(&fmtSize), 4);
    
    int16_t audioFormat = 1; // PCM
    file.write(reinterpret_cast<const char*>(&audioFormat), 2);
    
    file.write(reinterpret_cast<const char*>(&numChannels), 2);
    file.write(reinterpret_cast<const char*>(&sampleRate), 4);
    file.write(reinterpret_cast<const char*>(&byteRate), 4);
    file.write(reinterpret_cast<const char*>(&blockAlign), 2);
    file.write(reinterpret_cast<const char*>(&bitsPerSample), 2);
    
    file.write("data", 4);
    file.write(reinterpret_cast<const char*>(&dataSize), 4);
    
    // Write audio data
    for (float sample : recording_frames) {
        // Convert float to int16_t
        int16_t intSample = static_cast<int16_t>(sample * 32767.0f);
        file.write(reinterpret_cast<const char*>(&intSample), 2);
    }
    
    file.close();
    std::cout << "✅ Recording saved to " << filename << std::endl;
    std::cout << "📊 Duration: " << recording_frames.size() / (float)SAMPLE_RATE << "s" << std::endl;
}

int main(int argc, char* argv[]) {
    std::cout << "🎵 C++ Karaoke System with Dynamic Song Loading" << std::endl;
    std::cout << "💡 Tip: Use 'python3 song_finder.py --list' to see available songs" << std::endl;
    std::cout << "🚀 Recommended: Use 'python3 run_karaoke.py <song_name>' for best experience" << std::endl;
    
    // Check command line arguments
    if (argc < 2) {
        std::cout << "📖 Usage: " << argv[0] << " <song_name_or_melody_path> [instrumental_path] [voice_effects...]" << std::endl;
        std::cout << "🎵 Song options:" << std::endl;
        std::cout << "   song_name (looks for songs/song_name/song_name_melody.txt)" << std::endl;
        std::cout << "   path/to/melody.txt (full path to melody file)" << std::endl;
        std::cout << "   path/to/melody.txt path/to/instrumental.wav (both paths specified)" << std::endl;
        std::cout << "   song_name path/to/melody.txt path/to/instrumental.wav (new format)" << std::endl;
        std::cout << "🎤 Voice effect parameters (optional):" << std::endl;
        std::cout << "   autotune_strength (0.0-1.0) pitch_shift (-12 to +12) voice_volume (0.5-2.0) instrument_volume (0.0-2.0)" << std::endl;
        std::cout << "   enable_chorus (0/1) chorus_depth (0.0-1.0) enable_reverb (0/1) reverb_wetness (0.0-1.0)" << std::endl;
        std::cout << "💡 Examples:" << std::endl;
        std::cout << "   " << argv[0] << " Taylor_Swift_-_Love_Story" << std::endl;
        std::cout << "   " << argv[0] << " songs/my_song/my_song_melody.txt" << std::endl;
        std::cout << "   " << argv[0] << " melody.txt instrumental.wav" << std::endl;
        std::cout << "   " << argv[0] << " MySong melody.txt instrumental.wav" << std::endl;
        std::cout << "   " << argv[0] << " MySong melody.txt instrumental.wav 0.8 2 1.2 2.0 1 0.1 1 0.3" << std::endl;
        std::cout << "🔍 To see available songs: python3 song_finder.py --list" << std::endl;
        std::cout << "🚀 Recommended: python3 run_karaoke.py <song_name>" << std::endl;
        std::cout << "📁 Directory structure:" << std::endl;
        std::cout << "   songs/<song_name>/<name>_melody.txt" << std::endl;
        std::cout << "   songs/<song_name>/<name>_separated/<name>(Instrumental model_bs_roformer_ep_317_sdr_1).wav" << std::endl;
        return 1;
    }
    
    std::string song_name = argv[1];
    std::string melody_file;
    std::string instrumental_file;
    
    // Check if instrumental path is provided as third argument (new format: song_name, melody_file, instrumental_file)
    if (argc >= 4) {
        // New format: song_name, melody_file, instrumental_file
        melody_file = argv[2];
        instrumental_file = argv[3];
        std::cout << "🎵 Loading melody file: " << melody_file << std::endl;
        std::cout << "🎵 Loading instrumental file: " << instrumental_file << std::endl;
    } else if (argc >= 3) {
        // Old format: melody_file, instrumental_file (for backward compatibility)
        melody_file = argv[1];
        instrumental_file = argv[2];
        std::cout << "🎵 Loading melody file: " << melody_file << std::endl;
        std::cout << "🎵 Loading instrumental file: " << instrumental_file << std::endl;
    } else if (song_name.length() >= 4 && song_name.substr(song_name.length() - 4) == ".txt") {
        // If user provides a full path to melody file, use it directly
        melody_file = song_name;
        // Try to construct instrumental path from melody path
        std::string base_path = song_name.substr(0, song_name.find_last_of("/\\"));
        std::string base_name = base_path.substr(base_path.find_last_of("/\\") + 1);
        
        // Extract the actual song name from the directory name
        std::string actual_song_name;
        
        // Look for the pattern: songs/<complex_dir>/<song_name>_melody.txt
        // We need to extract <song_name> from the melody filename
        std::string melody_filename = song_name.substr(song_name.find_last_of("/\\") + 1);
        if (melody_filename.find("_melody.txt") != std::string::npos) {
            actual_song_name = melody_filename.substr(0, melody_filename.find("_melody.txt"));
        } else {
            // Fallback: try to clean the directory name
            actual_song_name = base_name;
            // Remove timestamp patterns
            size_t timestamp_pos = actual_song_name.find_last_of('_');
            if (timestamp_pos != std::string::npos) {
                std::string potential_timestamp = actual_song_name.substr(timestamp_pos + 1);
                if (potential_timestamp.length() == 15 && 
                    potential_timestamp.find_first_not_of("0123456789abcdef") == std::string::npos) {
                    actual_song_name = actual_song_name.substr(0, timestamp_pos);
                }
            }
            // Remove "Official_Video" suffix
            if (actual_song_name.length() > 13 && 
                actual_song_name.substr(actual_song_name.length() - 13) == "_Official_Video") {
                actual_song_name = actual_song_name.substr(0, actual_song_name.length() - 13);
            }
        }
        
        instrumental_file = base_path + "/" + actual_song_name + "_separated/" + actual_song_name + "(Instrumental model_bs_roformer_ep_317_sdr_1).wav";
        std::cout << "🎵 Loading custom melody file: " << song_name << std::endl;
        std::cout << "🔍 Looking for instrumental at: " << instrumental_file << std::endl;
    } else {
        // For song names, use the simplified pattern that works with Python script output
        // The Python script handles the complex directory structure, so we can use simple paths
        melody_file = "songs/" + song_name + "/" + song_name + "_melody.txt";
        instrumental_file = "songs/" + song_name + "/" + song_name + "_separated/" + song_name + "(Instrumental model_bs_roformer_ep_317_sdr_1).wav";
        std::cout << "🎵 Loading song: " << song_name << std::endl;
        std::cout << "💡 Tip: Use 'python3 song_finder.py " << song_name << "' to verify file paths" << std::endl;
        std::cout << "🚀 Recommended: Use 'python3 run_karaoke.py " << song_name << "' for best experience" << std::endl;
    }
    
    // Parse voice effect parameters from command line
    float autotune_strength = 1.0f;      // Default: full autotune
    float pitch_shift_amount = 0.0f;     // Default: no pitch shift
    float voice_volume = 1.1f;           // Default: slight voice boost
    float instrument_volume = 2.0f;      // Default: instrumental volume (was hardcoded 2.0f)
    bool enable_chorus = false;          // Default: no chorus
    float chorus_depth = 0.1f;           // Default: subtle chorus depth
    bool enable_reverb = false;          // Default: no reverb
    float reverb_wetness = 0.3f;         // Default: moderate reverb mix
    
    // Check if voice effect parameters are provided
    if (argc >= 4) {  // At minimum: song_name + melody_file + instrumental_file
        // Try to parse voice effect parameters if they exist
        int voice_param_start = 4;
        
        // Check if we have voice effect parameters
        if (argc >= voice_param_start + 8) {
            try {
                autotune_strength = std::stof(argv[voice_param_start]);
                pitch_shift_amount = std::stof(argv[voice_param_start + 1]);
                voice_volume = std::stof(argv[voice_param_start + 2]);
                instrument_volume = std::stof(argv[voice_param_start + 3]);
                enable_chorus = (std::stof(argv[voice_param_start + 4]) > 0.5f);
                chorus_depth = std::stof(argv[voice_param_start + 5]);
                enable_reverb = (std::stof(argv[voice_param_start + 6]) > 0.5f);
                reverb_wetness = std::stof(argv[voice_param_start + 7]);
                
                std::cout << "🎤 Voice Effect Parameters:" << std::endl;
                std::cout << "  Autotune Strength: " << autotune_strength << std::endl;
                std::cout << "  Pitch Shift: " << pitch_shift_amount << " semitones" << std::endl;
                std::cout << "  Voice Volume: " << voice_volume << std::endl;
                std::cout << "  Instrument Volume: " << instrument_volume << std::endl;
                std::cout << "  Chorus: " << (enable_chorus ? "Enabled" : "Disabled") << std::endl;
                std::cout << "  Chorus Depth: " << chorus_depth << std::endl;
                std::cout << "  Reverb: " << (enable_reverb ? "Enabled" : "Disabled") << std::endl;
                std::cout << "  Reverb Wetness: " << reverb_wetness << std::endl;
            } catch (const std::exception& e) {
                std::cout << "⚠️  Warning: Could not parse voice effect parameters: " << e.what() << std::endl;
                std::cout << "🎤 Using default voice effect settings" << std::endl;
            }
        } else {
            std::cout << "🎤 Using default voice effect settings" << std::endl;
        }
    }
    
    // Initialize SDL2 for plotting
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        std::cerr << "❌ SDL2 initialization failed: " << SDL_GetError() << std::endl;
        return 1;
    }
    
    SDL_Window* window = SDL_CreateWindow("Karaoke Pitch Plot", 
                                         SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
                                         PLOT_WIDTH, PLOT_HEIGHT, SDL_WINDOW_SHOWN);
    if (!window) {
        std::cerr << "❌ Could not create window: " << SDL_GetError() << std::endl;
        SDL_Quit();
        return 1;
    }
    
    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (!renderer) {
        std::cerr << "❌ Could not create renderer: " << SDL_GetError() << std::endl;
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    
    // Initialize PortAudio
    PaError err = Pa_Initialize();
    if (err != paNoError) {
        std::cerr << "❌ PortAudio initialization failed: " << Pa_GetErrorText(err) << std::endl;
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    
    // Load instrumental audio
    std::cout << "🎼 Loading instrumental..." << std::endl;
    SF_INFO sfinfo;
    sfinfo.format = 0;
    SNDFILE* sndfile = sf_open(instrumental_file.c_str(), SFM_READ, &sfinfo);
    if (!sndfile) {
        std::cerr << "❌ Could not open instrumental file: " << instrumental_file << std::endl;
        std::cerr << "💡 Try using: python3 song_finder.py " << song_name << std::endl;
        std::cerr << "🚀 Or use: python3 run_karaoke.py " << song_name << std::endl;
        Pa_Terminate();
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    
    std::cout << "📊 WAV Info - Channels: " << sfinfo.channels << ", Sample Rate: " << sfinfo.samplerate << "Hz, Frames: " << sfinfo.frames << std::endl;
    
    // Handle stereo files by converting to mono and resampling if needed
    std::vector<float> instrumental;
    if (sfinfo.channels == 2) {
        // Stereo file - read all samples and convert to mono
        std::vector<float> stereo_data(sfinfo.frames * sfinfo.channels);
        sf_read_float(sndfile, stereo_data.data(), sfinfo.frames * sfinfo.channels);
        
        // Convert stereo to mono by averaging channels
        instrumental.resize(sfinfo.frames);
        for (int i = 0; i < sfinfo.frames; i++) {
            instrumental[i] = (stereo_data[i * 2] + stereo_data[i * 2 + 1]) * 0.5f;
        }
        std::cout << "🔄 Converted stereo to mono" << std::endl;
    } else {
        // Mono file - read directly
        instrumental.resize(sfinfo.frames);
        sf_read_float(sndfile, instrumental.data(), sfinfo.frames);
    }
    
    // Resample if sample rate doesn't match target
    if (sfinfo.samplerate != SAMPLE_RATE) {
        std::cout << "🔄 Resampling from " << sfinfo.samplerate << "Hz to " << SAMPLE_RATE << "Hz" << std::endl;
        
        // Simple linear interpolation resampling
        float ratio = (float)SAMPLE_RATE / sfinfo.samplerate;
        int new_size = (int)(instrumental.size() * ratio);
        std::vector<float> resampled(new_size);
        
        for (int i = 0; i < new_size; i++) {
            float old_pos = i / ratio;
            int old_idx = (int)old_pos;
            float fraction = old_pos - old_idx;
            
            if (old_idx >= (int)instrumental.size() - 1) {
                resampled[i] = instrumental.back();
            } else {
                resampled[i] = instrumental[old_idx] * (1.0f - fraction) + instrumental[old_idx + 1] * fraction;
            }
        }
        
        instrumental = std::move(resampled);
        std::cout << "✅ Resampled to " << instrumental.size() << " samples" << std::endl;
    }
    
    sf_close(sndfile);
    std::cout << "✅ Loaded " << instrumental.size() << " samples" << std::endl;
    
    // Load melody map from generated header
    std::vector<std::pair<float, float>> melody_map = loadMelodyMap(melody_file);
    
    if (melody_map.empty()) {
        std::cerr << "❌ Failed to load melody map from: " << melody_file << std::endl;
        std::cerr << "💡 Try using: python3 song_finder.py " << song_name << std::endl;
        std::cerr << "🚀 Or use: python3 run_karaoke.py " << song_name << std::endl;
        Pa_Terminate();
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    
    // Initialize aubio pitch detector with safe parameters
    aubio_pitch_t* pitch_detector = new_aubio_pitch("default", 2048, FRAMES_PER_BUFFER, SAMPLE_RATE);
    if (!pitch_detector) {
        std::cerr << "❌ Failed to create aubio pitch detector!" << std::endl;
        Pa_Terminate();
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    aubio_pitch_set_unit(pitch_detector, "Hz");
    aubio_pitch_set_silence(pitch_detector, -50);  // Lower silence threshold for better detection
    
    // Initialize noise suppressor
    SimpleNoiseSuppressor* noise_suppressor = new SimpleNoiseSuppressor();
    if (!noise_suppressor) {
        std::cerr << "❌ Failed to create noise suppressor!" << std::endl;
        del_aubio_pitch(pitch_detector);
        Pa_Terminate();
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    
    // Initialize and configure noise suppressor
    noise_suppressor->init(SAMPLE_RATE);
    noise_suppressor->setNoiseGateThreshold(0.01f);  // 1% threshold
    noise_suppressor->setVADThreshold(0.3f);         // 30% VAD threshold
    noise_suppressor->setGracePeriod(200);           // 200ms grace period
    noise_suppressor->setNoiseReductionStrength(0.6f); // 60% noise reduction
    
    // Setup audio data
    AudioData audio_data;
    audio_data.instrumental = instrumental;
    audio_data.instrumental_pos = 0;
    audio_data.melody_map = melody_map;
    audio_data.current_time = 0.0f;
    audio_data.pitch_detector = pitch_detector;
    audio_data.last_pitch = 0.0f;
    audio_data.last_confidence = 0.0f;
    audio_data.recording_enabled = true;  // Enable recording
    audio_data.recording_frames.clear();
    audio_data.noise_suppressor = noise_suppressor; // Assign noise suppressor
    
    // Initialize voice effect parameters with parsed values
    audio_data.autotune_strength = autotune_strength;
    audio_data.pitch_shift_amount = pitch_shift_amount;
    audio_data.voice_volume = voice_volume;
    audio_data.instrument_volume = instrument_volume;
    audio_data.enable_chorus = enable_chorus;
    audio_data.chorus_depth = chorus_depth;
    audio_data.enable_reverb = enable_reverb;
    audio_data.reverb_wetness = reverb_wetness;
    
    // Find audio devices
    PaDeviceIndex inputDevice = findDefaultInputDevice();
    PaDeviceIndex outputDevice = findDefaultOutputDevice();
    
    if (inputDevice == paNoDevice) {
        std::cerr << "❌ No input device found!" << std::endl;
        del_aubio_pitch(pitch_detector);
        delete noise_suppressor; // Clean up noise suppressor
        Pa_Terminate();
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    
    if (outputDevice == paNoDevice) {
        std::cerr << "❌ No output device found!" << std::endl;
        del_aubio_pitch(pitch_detector);
        delete noise_suppressor; // Clean up noise suppressor
        Pa_Terminate();
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    
    // Setup input parameters
    PaStreamParameters inputParameters;
    inputParameters.device = inputDevice;
    inputParameters.channelCount = NUM_CHANNELS;
    inputParameters.sampleFormat = paFloat32;
    inputParameters.suggestedLatency = Pa_GetDeviceInfo(inputDevice)->defaultLowInputLatency;
    inputParameters.hostApiSpecificStreamInfo = nullptr;
    
    // Setup output parameters
    PaStreamParameters outputParameters;
    outputParameters.device = outputDevice;
    outputParameters.channelCount = NUM_CHANNELS;
    outputParameters.sampleFormat = paFloat32;
    outputParameters.suggestedLatency = Pa_GetDeviceInfo(outputDevice)->defaultLowOutputLatency;
    outputParameters.hostApiSpecificStreamInfo = nullptr;
    
    // Open audio stream
    PaStream* stream;
    
    // Debug: Print device info
    const PaDeviceInfo* inputDeviceInfo = Pa_GetDeviceInfo(inputDevice);
    const PaDeviceInfo* outputDeviceInfo = Pa_GetDeviceInfo(outputDevice);
    
    std::cout << "🎤 Input device: " << inputDeviceInfo->name << " (channels: " << inputDeviceInfo->maxInputChannels << ")" << std::endl;
    std::cout << "🔊 Output device: " << outputDeviceInfo->name << " (channels: " << outputDeviceInfo->maxOutputChannels << ")" << std::endl;
    std::cout << "⚙️  Sample rate: " << SAMPLE_RATE << "Hz, Buffer size: " << FRAMES_PER_BUFFER << std::endl;
    
    err = Pa_OpenStream(&stream,
                        &inputParameters,
                        &outputParameters,
                        SAMPLE_RATE,
                        FRAMES_PER_BUFFER,
                        paClipOff,
                        audioCallback, &audio_data);
    
    if (err != paNoError) {
        std::cerr << "❌ Could not open audio stream: " << Pa_GetErrorText(err) << std::endl;
        del_aubio_pitch(pitch_detector);
        delete noise_suppressor; // Clean up noise suppressor
        Pa_Terminate();
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    
    // Start stream
    err = Pa_StartStream(stream);
    if (err != paNoError) {
        std::cerr << "❌ Could not start stream: " << Pa_GetErrorText(err) << std::endl;
        Pa_CloseStream(stream);
        del_aubio_pitch(pitch_detector);
        delete noise_suppressor; // Clean up noise suppressor
        Pa_Terminate();
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    
    // Extract clean song name for filename
    std::string clean_song_name = song_name;
    
    // If it's a full path, extract just the song name
    if (song_name.find('/') != std::string::npos) {
        // Find the last directory name in the path
        size_t last_slash = song_name.find_last_of("/\\");
        if (last_slash != std::string::npos) {
            clean_song_name = song_name.substr(last_slash + 1);
            // Remove any file extensions
            size_t dot_pos = clean_song_name.find('.');
            if (dot_pos != std::string::npos) {
                clean_song_name = clean_song_name.substr(0, dot_pos);
            }
        }
    }
    
    // Generate unique filename for this session
    std::string output_filename = generateUniqueFilename(clean_song_name);
    
    std::cout << "🎤 C++ Karaoke with Recording started! Sing into your microphone..." << std::endl;
    std::cout << "🛑 Press Ctrl+C to stop" << std::endl;
    std::cout << "📊 Green line = Your pitch, Red line = Target melody" << std::endl;
    std::cout << "📹 Recording will be saved to " << output_filename << std::endl;
    
    // Main loop with plotting
    auto start_time = std::chrono::high_resolution_clock::now();
    SDL_Event event;
    bool quit = false;
    
    while (!quit) {
        // Handle SDL events
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                quit = true;
            }
        }
        
        // Draw the plot
        drawPlot(renderer, audio_data);
        
        // Print debug info every 2 seconds
        auto now = std::chrono::high_resolution_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - start_time).count();
        
        if (elapsed % 2 == 0 && elapsed > 0) {
            std::cout << "⏱️  " << elapsed << "s | 🎤 Pitch: " << audio_data.last_pitch 
                      << "Hz | Confidence: " << audio_data.last_confidence 
                      << " | Target: " << (audio_data.target_history.empty() ? 0.0f : audio_data.target_history.back()) << "Hz" << std::endl;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(50)); // 20 FPS
    }
    
    // Save recording
    if (!audio_data.recording_frames.empty()) {
        std::cout << "💾 Saving recording..." << std::endl;
        saveRecording(audio_data.recording_frames, output_filename);
    }
    
    // Cleanup
    Pa_StopStream(stream);
    Pa_CloseStream(stream);
    del_aubio_pitch(pitch_detector);
    delete noise_suppressor; // Clean up noise suppressor
    Pa_Terminate();
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    
    std::cout << "✅ Cleanup complete!" << std::endl;
    return 0;
} 