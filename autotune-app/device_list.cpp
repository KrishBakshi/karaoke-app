#include <iostream>
#include <vector>
#include <string>
#include <portaudio.h>

struct AudioDevice {
    int index;
    std::string name;
    int maxChannels;
    bool isInput;
};

void listAudioDevices() {
    std::cout << "🔍 Available Audio Devices:" << std::endl;
    
    int numDevices = Pa_GetDeviceCount();
    if (numDevices < 0) {
        std::cerr << "❌ Error getting device count: " << Pa_GetErrorText(numDevices) << std::endl;
        return;
    }
    
    std::vector<AudioDevice> inputDevices;
    std::vector<AudioDevice> outputDevices;
    
    for (int i = 0; i < numDevices; i++) {
        const PaDeviceInfo* deviceInfo = Pa_GetDeviceInfo(i);
        if (!deviceInfo) continue;
        
        if (deviceInfo->maxInputChannels > 0) {
            inputDevices.push_back({i, deviceInfo->name, deviceInfo->maxInputChannels, true});
        }
        
        if (deviceInfo->maxOutputChannels > 0) {
            outputDevices.push_back({i, deviceInfo->name, deviceInfo->maxOutputChannels, false});
        }
    }
    
    std::cout << "\n🎤 Input Devices (Microphones):" << std::endl;
    for (const auto& device : inputDevices) {
        std::cout << "   [" << device.index << "] " << device.name 
                  << " (channels: " << device.maxChannels << ")" << std::endl;
    }
    
    std::cout << "\n🔊 Output Devices (Speakers/Headphones):" << std::endl;
    for (const auto& device : outputDevices) {
        std::cout << "   [" << device.index << "] " << device.name 
                  << " (channels: " << device.maxChannels << ")" << std::endl;
    }
    
    std::cout << "\n💡 To use specific devices with karaoke:" << std::endl;
    std::cout << "   ./karaoke <song_name> \"<input_device_name>\" \"<output_device_name>\"" << std::endl;
    std::cout << "   Example: ./karaoke Taylor_Swift_-_Love_Story \"USB Microphone\" \"USB Headphones\"" << std::endl;
}

void findDeviceByName(const std::string& deviceName, bool isInput) {
    int numDevices = Pa_GetDeviceCount();
    if (numDevices < 0) {
        std::cerr << "❌ Error getting device count: " << Pa_GetErrorText(numDevices) << std::endl;
        return;
    }
    
    for (int i = 0; i < numDevices; i++) {
        const PaDeviceInfo* deviceInfo = Pa_GetDeviceInfo(i);
        if (!deviceInfo) continue;
        
        if (isInput && deviceInfo->maxInputChannels > 0) {
            if (deviceInfo->name == deviceName) {
                std::cout << "✅ Found input device [" << i << "]: " << deviceInfo->name << std::endl;
                return;
            }
        } else if (!isInput && deviceInfo->maxOutputChannels > 0) {
            if (deviceInfo->name == deviceName) {
                std::cout << "✅ Found output device [" << i << "]: " << deviceInfo->name << std::endl;
                return;
            }
        }
    }
    
    std::cout << "❌ Device not found: " << deviceName << std::endl;
}

int main(int argc, char* argv[]) {
    std::cout << "🎵 Audio Device Manager for Karaoke System" << std::endl;
    
    // Initialize PortAudio
    PaError err = Pa_Initialize();
    if (err != paNoError) {
        std::cerr << "❌ PortAudio initialization failed: " << Pa_GetErrorText(err) << std::endl;
        return 1;
    }
    
    if (argc == 1) {
        // Just list devices
        listAudioDevices();
    } else if (argc == 3) {
        // Check specific devices
        std::string inputDevice = argv[1];
        std::string outputDevice = argv[2];
        
        std::cout << "\n🔍 Checking specified devices:" << std::endl;
        findDeviceByName(inputDevice, true);
        findDeviceByName(outputDevice, false);
        
        std::cout << "\n💡 To run karaoke with these devices:" << std::endl;
        std::cout << "   ./karaoke <song_name> \"" << inputDevice << "\" \"" << outputDevice << "\"" << std::endl;
    } else {
        std::cout << "Usage:" << std::endl;
        std::cout << "  " << argv[0] << "                    # List all devices" << std::endl;
        std::cout << "  " << argv[0] << " \"input\" \"output\"  # Check specific devices" << std::endl;
        std::cout << "\nExamples:" << std::endl;
        std::cout << "  " << argv[0] << std::endl;
        std::cout << "  " << argv[0] << " \"USB Microphone\" \"USB Headphones\"" << std::endl;
    }
    
    // Cleanup
    Pa_Terminate();
    return 0;
}
