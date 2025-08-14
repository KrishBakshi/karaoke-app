#ifndef SIMPLE_NOISE_SUPPRESSION_H
#define SIMPLE_NOISE_SUPPRESSION_H

#include <vector>
#include <deque>
#include <cmath>

class SimpleNoiseSuppressor {
public:
    SimpleNoiseSuppressor();
    
    // Initialize with sample rate
    void init(int sampleRate = 48000);
    
    // Process audio samples
    void processAudio(float* input, float* output, int numSamples);
    
    // Set noise gate threshold (0.0 to 1.0)
    void setNoiseGateThreshold(float threshold);
    
    // Set VAD threshold (0.0 to 1.0)
    void setVADThreshold(float threshold);
    
    // Set grace period in milliseconds
    void setGracePeriod(int ms);
    
    // Set noise reduction strength (0.0 to 1.0)
    void setNoiseReductionStrength(float strength);
    
    // Get current VAD probability
    float getVADProbability() const;
    
    // Get noise level estimate
    float getNoiseLevel() const;
    
    // Reset the suppressor
    void reset();
    
    // Check if voice is detected
    bool isVoiceActive() const;

private:
    // Audio processing parameters
    int m_sampleRate;
    float m_noiseGateThreshold;
    float m_vadThreshold;
    int m_gracePeriod;
    float m_noiseReductionStrength;
    
    // Noise estimation
    std::deque<float> m_noiseHistory;
    float m_noiseLevel;
    float m_signalLevel;
    
    // VAD (Voice Activity Detection)
    float m_vadProbability;
    bool m_voiceActive;
    int m_graceCounter;
    bool m_inGracePeriod;
    
    // Audio buffers for processing
    std::vector<float> m_inputBuffer;
    std::vector<float> m_outputBuffer;
    
    // Processing methods
    float estimateNoiseLevel(const float* samples, int numSamples);
    float estimateSignalLevel(const float* samples, int numSamples);
    float calculateVADProbability(float signalLevel, float noiseLevel);
    void applyNoiseGate(float* samples, int numSamples);
    void applySpectralNoiseReduction(float* samples, int numSamples);
    
    // Simple spectral analysis
    std::vector<float> m_spectrum;
    void computeSpectrum(const float* samples, int numSamples);
    
    // Constants
    static constexpr size_t NOISE_HISTORY_SIZE = 1000;
    static constexpr float MIN_NOISE_LEVEL = 0.001f;
    static constexpr float MAX_NOISE_LEVEL = 0.5f;
};

#endif // SIMPLE_NOISE_SUPPRESSION_H
