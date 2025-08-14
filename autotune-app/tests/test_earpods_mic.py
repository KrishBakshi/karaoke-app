import pyaudio
import numpy as np
import time

print("🎤 Testing EarPods microphone...")

p = pyaudio.PyAudio()

# Use EarPods (device 6) at 48kHz
INPUT_DEVICE = 6
RATE = 48000

print(f"Using device {INPUT_DEVICE}: EarPods: USB Audio")

stream = p.open(format=pyaudio.paFloat32, 
                channels=1, 
                rate=RATE, 
                input=True, 
                input_device_index=INPUT_DEVICE,
                frames_per_buffer=1024)

print("🎤 Speak into your EarPods microphone! (Press Ctrl+C to stop)")
print("💡 Make sure your EarPods are properly connected")

try:
    for i in range(200):  # Test for about 4 seconds
        data = stream.read(1024, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.float32)
        volume = np.sqrt(np.mean(samples**2))
        
        if i % 20 == 0:  # Print every 0.4 seconds
            print(f"📊 Volume level: {volume:.4f} {'🔊' if volume > 0.01 else '🔇'}")
        
        time.sleep(0.02)

except KeyboardInterrupt:
    print("\n🛑 Microphone test stopped.")

stream.stop_stream()
stream.close()
p.terminate()

print("✅ EarPods microphone test complete!") 