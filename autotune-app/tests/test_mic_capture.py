import pyaudio
import numpy as np
import time

print("🎤 Testing Microphone Capture...")

# Configuration
CHUNK = 1024
RATE = 48000
FORMAT = pyaudio.paFloat32
CHANNELS = 1
INPUT_DEVICE = 0  # EarPods

p = pyaudio.PyAudio()

print(f"🎤 Using input device {INPUT_DEVICE} (EarPods)")
print("🔊 Speak into your microphone...")

try:
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, input_device_index=INPUT_DEVICE,
                    frames_per_buffer=CHUNK)
    
    print("✅ Microphone stream created")
    print("🎤 Speak now! (Press Ctrl+C to stop)")
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.float32)
        
        # Calculate audio levels
        rms = np.sqrt(np.mean(samples**2))
        peak = np.max(np.abs(samples))
        
        frame_count += 1
        elapsed = time.time() - start_time
        
        # Print levels every 50 frames (about every second)
        if frame_count % 50 == 0:
            print(f"⏱️  {elapsed:.1f}s | 🔊 RMS: {rms:.3f} | 📊 Peak: {peak:.3f} | {'🎤 VOICE DETECTED!' if rms > 0.01 else '🔇 No voice'}")
        
        # Stop after 10 seconds
        if elapsed > 10:
            break
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("✅ Microphone test complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    p.terminate() 