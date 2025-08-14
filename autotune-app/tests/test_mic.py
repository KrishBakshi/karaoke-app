import pyaudio
import numpy as np
import time

# Test microphone
print("🎤 Testing microphone...")

p = pyaudio.PyAudio()

# Use device 5 (your laptop's built-in mic)
INPUT_DEVICE = 5

print(f"Using device {INPUT_DEVICE}: HD-Audio Generic: ALC256 Analog")

stream = p.open(format=pyaudio.paFloat32, 
                channels=1, 
                rate=44100, 
                input=True, 
                input_device_index=INPUT_DEVICE,
                frames_per_buffer=1024)

print("🎤 Speak into your microphone! (Press Ctrl+C to stop)")

try:
    for i in range(100):  # Test for about 2 seconds
        data = stream.read(1024, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.float32)
        volume = np.sqrt(np.mean(samples**2))
        
        if i % 10 == 0:  # Print every 0.2 seconds
            print(f"📊 Volume level: {volume:.4f} {'🔊' if volume > 0.01 else '🔇'}")
        
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\n🛑 Microphone test stopped.")

stream.stop_stream()
stream.close()
p.terminate()

print("✅ Microphone test complete!") 