#include "simple_noise_suppression.h"
#include <algorithm>
#include <numeric>
#include <iostream>

SimpleNoiseSuppressor::SimpleNoiseSuppressor()
    : m_sampleRate(48000)
    , m_noiseGateThreshold(0.01f)
    , m_vadThreshold(0.3f)
    , m_gracePeriod(200)
    , m_noiseReductionStrength(0.5f)
    , m_noiseLevel(0.001f)
    , m_signalLevel(0.0f)
    , m_vadProbability(0.0f)
    , m_voiceActive(false)
    , m_graceCounter(0)
    , m_inGracePeriod(false)
{
    m_noiseHistory.resize(NOISE_HISTORY_SIZE, 0.0f);
    m_spectrum.resize(256, 0.0f);
}

void SimpleNoiseSuppressor::init(int sampleRate) {
    m_sampleRate = sampleRate;
    reset();
    std::cout << "🔇 Noise suppressor initialized at " << sampleRate << " Hz" << std::endl;
}

void SimpleNoiseSuppressor::processAudio(float* input, float* output, int numSamples) {
    if (numSamples <= 0) return;
    
    // Copy input to output initially
    std::copy(input, input + numSamples, output);
    
    // Estimate noise and signal levels
    m_noiseLevel = estimateNoiseLevel(input, numSamples);
    m_signalLevel = estimateSignalLevel(input, numSamples);
    
    // Calculate VAD probability
    m_vadProbability = calculateVADProbability(m_signalLevel, m_noiseLevel);
    
    // Update voice activity status
    bool wasVoiceActive = m_voiceActive;
    m_voiceActive = (m_vadProbability > m_vadThreshold);
    
    // Handle grace period
    if (m_voiceActive) {
        m_graceCounter = m_gracePeriod;
        m_inGracePeriod = true;
    } else if (m_inGracePeriod) {
        m_graceCounter -= (numSamples * 1000) / m_sampleRate; // Convert samples to ms
        if (m_graceCounter <= 0) {
            m_inGracePeriod = false;
        }
    }
    
    // Apply noise gate if no voice activity
    if (!m_voiceActive && !m_inGracePeriod) {
        applyNoiseGate(output, numSamples);
    }
    
    // Apply spectral noise reduction
    if (m_noiseReductionStrength > 0.0f) {
        applySpectralNoiseReduction(output, numSamples);
    }
}

void SimpleNoiseSuppressor::setNoiseGateThreshold(float threshold) {
    m_noiseGateThreshold = std::clamp(threshold, 0.0f, 1.0f);
    std::cout << "🔇 Noise gate threshold set to: " << m_noiseGateThreshold << std::endl;
}

void SimpleNoiseSuppressor::setVADThreshold(float threshold) {
    m_vadThreshold = std::clamp(threshold, 0.0f, 1.0f);
    std::cout << "🎤 VAD threshold set to: " << m_vadThreshold << std::endl;
}

void SimpleNoiseSuppressor::setGracePeriod(int ms) {
    m_gracePeriod = std::max(0, ms);
    std::cout << "⏱️  Grace period set to: " << m_gracePeriod << " ms" << std::endl;
}

void SimpleNoiseSuppressor::setNoiseReductionStrength(float strength) {
    m_noiseReductionStrength = std::clamp(strength, 0.0f, 1.0f);
    std::cout << "🔊 Noise reduction strength set to: " << m_noiseReductionStrength << std::endl;
}

float SimpleNoiseSuppressor::getVADProbability() const {
    return m_vadProbability;
}

float SimpleNoiseSuppressor::getNoiseLevel() const {
    return m_noiseLevel;
}

bool SimpleNoiseSuppressor::isVoiceActive() const {
    return m_voiceActive || m_inGracePeriod;
}

void SimpleNoiseSuppressor::reset() {
    m_noiseLevel = MIN_NOISE_LEVEL;
    m_signalLevel = 0.0f;
    m_vadProbability = 0.0f;
    m_voiceActive = false;
    m_graceCounter = 0;
    m_inGracePeriod = false;
    
    std::fill(m_noiseHistory.begin(), m_noiseHistory.end(), 0.0f);
    std::fill(m_spectrum.begin(), m_spectrum.end(), 0.0f);
}

float SimpleNoiseSuppressor::estimateNoiseLevel(const float* samples, int numSamples) {
    // Calculate RMS of the signal
    float sum = 0.0f;
    for (int i = 0; i < numSamples; ++i) {
        sum += samples[i] * samples[i];
    }
    float rms = std::sqrt(sum / numSamples);
    
    // Update noise history (sliding window)
    m_noiseHistory.push_back(rms);
    m_noiseHistory.pop_front();
    
    // Calculate median noise level (more robust than mean)
    std::vector<float> sortedNoise(m_noiseHistory.begin(), m_noiseHistory.end());
    std::sort(sortedNoise.begin(), sortedNoise.end());
    float medianNoise = sortedNoise[sortedNoise.size() / 2];
    
    // Smooth the noise level estimate
    m_noiseLevel = 0.95f * m_noiseLevel + 0.05f * medianNoise;
    
    // Clamp to reasonable range
    m_noiseLevel = std::clamp(m_noiseLevel, MIN_NOISE_LEVEL, MAX_NOISE_LEVEL);
    
    return m_noiseLevel;
}

float SimpleNoiseSuppressor::estimateSignalLevel(const float* samples, int numSamples) {
    // Calculate RMS of the signal
    float sum = 0.0f;
    for (int i = 0; i < numSamples; ++i) {
        sum += samples[i] * samples[i];
    }
    float rms = std::sqrt(sum / numSamples);
    
    // Smooth the signal level estimate
    m_signalLevel = 0.9f * m_signalLevel + 0.1f * rms;
    
    return m_signalLevel;
}

float SimpleNoiseSuppressor::calculateVADProbability(float signalLevel, float noiseLevel) {
    if (noiseLevel < MIN_NOISE_LEVEL) {
        return 1.0f; // Assume voice if no noise detected
    }
    
    // Calculate signal-to-noise ratio
    float snr = signalLevel / noiseLevel;
    
    // Convert SNR to probability using sigmoid function
    float probability = 1.0f / (1.0f + std::exp(-5.0f * (snr - 2.0f)));
    
    return std::clamp(probability, 0.0f, 1.0f);
}

void SimpleNoiseSuppressor::applyNoiseGate(float* samples, int numSamples) {
    for (int i = 0; i < numSamples; ++i) {
        if (std::abs(samples[i]) < m_noiseGateThreshold) {
            samples[i] = 0.0f;
        }
    }
}

void SimpleNoiseSuppressor::applySpectralNoiseReduction(float* samples, int numSamples) {
    // Simple frequency-domain noise reduction
    // This is a simplified version - real implementations use FFT
    
    // Apply high-pass filter to reduce low-frequency noise
    static float prevSample = 0.0f;
    float cutoffFreq = 80.0f; // Hz
    float rc = 1.0f / (2.0f * M_PI * cutoffFreq);
    float dt = 1.0f / m_sampleRate;
    float alpha = rc / (rc + dt);
    
    for (int i = 0; i < numSamples; ++i) {
        float currentSample = samples[i];
        samples[i] = alpha * (prevSample + currentSample - prevSample);
        prevSample = currentSample;
    }
    
    // Apply noise reduction based on VAD
    if (!m_voiceActive) {
        float reductionFactor = 1.0f - m_noiseReductionStrength;
        for (int i = 0; i < numSamples; ++i) {
            samples[i] *= reductionFactor;
        }
    }
}

void SimpleNoiseSuppressor::computeSpectrum(const float* samples, int numSamples) {
    // Simplified spectrum computation (real implementations use FFT)
    // This is just a placeholder for more advanced spectral processing
    
    // Reset spectrum
    std::fill(m_spectrum.begin(), m_spectrum.end(), 0.0f);
    
    // Simple frequency analysis (very basic)
    for (int i = 0; i < numSamples && i < 256; ++i) {
        int bin = (i * 256) / numSamples;
        if (bin < 256) {
            m_spectrum[bin] += std::abs(samples[i]);
        }
    }
}
