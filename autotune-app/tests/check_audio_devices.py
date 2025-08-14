import pyaudio
import numpy as np

print("🔍 Checking audio device capabilities...")

p = pyaudio.PyAudio()

# Test sample rates
test_rates = [8000, 16000, 22050, 44100, 48000, 96000]

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"\n📱 Device {i}: {info['name']}")
    print(f"   Max input channels: {info['maxInputChannels']}")
    print(f"   Max output channels: {info['maxOutputChannels']}")
    
    if info['maxInputChannels'] > 0:
        print("   Supported input sample rates:")
        for rate in test_rates:
            try:
                stream = p.open(format=pyaudio.paFloat32,
                              channels=1,
                              rate=rate,
                              input=True,
                              input_device_index=i,
                              frames_per_buffer=1024)
                stream.close()
                print(f"     ✅ {rate}Hz")
            except Exception as e:
                print(f"     ❌ {rate}Hz - {e}")
    
    if info['maxOutputChannels'] > 0:
        print("   Supported output sample rates:")
        for rate in test_rates:
            try:
                stream = p.open(format=pyaudio.paFloat32,
                              channels=1,
                              rate=rate,
                              output=True,
                              output_device_index=i,
                              frames_per_buffer=1024)
                stream.close()
                print(f"     ✅ {rate}Hz")
            except Exception as e:
                print(f"     ❌ {rate}Hz - {e}")

p.terminate()
print("\n✅ Device check complete!") 