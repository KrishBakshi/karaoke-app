import pyaudio
import numpy as np
import soundfile as sf
import time

print("🎵 Testing WAV Playback (No Processing)")

# Configuration
CHUNK = 512
RATE = 48000
FORMAT = pyaudio.paFloat32
CHANNELS = 1
OUTPUT_DEVICE = 6  # EarPods: USB Audio

# Load WAV file
print("🎼 Loading WAV file...")
try:
    audio_data, sr = sf.read("blinding_lights_instrumental.wav", dtype='float32')
    print(f"✅ Loaded {len(audio_data)} samples at {sr}Hz")
    
    # Ensure it's mono
    if len(audio_data.shape) > 1:
        audio_data = audio_data[:, 0]
    
    print("✅ Audio loaded successfully")
except Exception as e:
    print(f"❌ Error loading WAV: {e}")
    exit(1)

# Setup audio output only
print("🔊 Setting up audio output...")
p = pyaudio.PyAudio()

try:
    stream_out = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        output=True, output_device_index=OUTPUT_DEVICE,
                        frames_per_buffer=CHUNK)
    print("✅ Output stream created")
except Exception as e:
    print(f"❌ Output error: {e}")
    exit(1)

print("🎤 Playing instrumental (no processing)...")
print("💡 You should hear smooth playback with no lag")
print("🛑 Press Ctrl+C to stop")

pos = 0
start_time = time.time()

try:
    while True:
        # Get chunk
        end_pos = pos + CHUNK
        
        if end_pos > len(audio_data):
            # Loop back to start
            chunk1 = audio_data[pos:]
            chunk2 = audio_data[:end_pos - len(audio_data)]
            chunk = np.concatenate([chunk1, chunk2])
            pos = end_pos - len(audio_data)
        else:
            chunk = audio_data[pos:end_pos]
            pos = end_pos
        
        # Play chunk
        stream_out.write(chunk.astype(np.float32).tobytes())
        
        # Simple timing check
        elapsed = time.time() - start_time
        if int(elapsed) % 10 == 0 and int(elapsed) > 0:
            print(f"⏱️  {elapsed:.1f}s - Playing smoothly")

except KeyboardInterrupt:
    print("\n🛑 Stopping playback...")

finally:
    stream_out.stop_stream()
    stream_out.close()
    p.terminate()
    print("✅ Cleanup complete!") 