#include <iostream>
#include <fstream>
#include <string>

int main() {
    std::cout << "🧪 Testing parameter file reading..." << std::endl;
    
    std::ifstream param_file("voice_params.txt");
    if (!param_file.is_open()) {
        std::cerr << "❌ Could not open voice_params.txt" << std::endl;
        return 1;
    }
    
    std::string line;
    while (std::getline(param_file, line)) {
        if (line.find("instrument_volume=") == 0) {
            float value = std::stof(line.substr(18));
            std::cout << "🎛️ Instrument volume: " << value << std::endl;
        } else if (line.find("voice_volume=") == 0) {
            float value = std::stof(line.substr(13));
            std::cout << "🎤 Voice volume: " << value << std::endl;
        }
    }
    
    param_file.close();
    std::cout << "✅ Parameter file read successfully" << std::endl;
    return 0;
}
