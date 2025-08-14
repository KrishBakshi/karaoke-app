import pyaudio
import numpy as np
import time
import soundfile as sf
from scipy.signal import resample
import matplotlib.pyplot as plt
from collections import deque
import aubio
import threading

print("🎵 Smooth Karaoke System (Preloaded Audio)")

# Configuration
CHUNK = 512  # Slightly larger for smoother playback
RATE = 48000
FORMAT = pyaudio.paFloat32
CHANNELS = 1
INPUT_DEVICE = 6   # EarPods: USB Audio
OUTPUT_DEVICE = 6  # EarPods: USB Audio

# Preload WAV instrumental into memory
print("🎼 Preloading WAV instrumental...")
try:
    instr_audio, instr_sr = sf.read("blinding_lights_instrumental.wav", dtype='float32')
    print(f"✅ Loaded {len(instr_audio)} samples at {instr_sr}Hz")
    print(f"✅ Duration: {len(instr_audio)/instr_sr:.1f} seconds")
    
    # Ensure it's mono
    if len(instr_audio.shape) > 1:
        instr_audio = instr_audio[:, 0]
    
    # Create a circular buffer for smooth looping
    instr_pos = 0
    print("✅ Audio preloaded into memory")
except Exception as e:
    print(f"❌ Error loading WAV: {e}")
    exit(1)

def get_instrumental_chunk():
    global instr_pos
    end_pos = instr_pos + CHUNK
    
    if end_pos > len(instr_audio):
        # Need to wrap around
        chunk1 = instr_audio[instr_pos:]
        chunk2 = instr_audio[:end_pos - len(instr_audio)]
        chunk = np.concatenate([chunk1, chunk2])
        instr_pos = end_pos - len(instr_audio)
    else:
        chunk = instr_audio[instr_pos:end_pos]
        instr_pos = end_pos
    
    return chunk

# Setup audio
print("🔊 Setting up audio...")
p = pyaudio.PyAudio()

print(f"🎤 Using input device {INPUT_DEVICE} (EarPods)")
print(f"🔊 Using output device {OUTPUT_DEVICE} (EarPods)")
print(f"⚡ Buffer size: {CHUNK} samples ({CHUNK/RATE*1000:.1f}ms latency)")

try:
    stream_in = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                       input=True, input_device_index=INPUT_DEVICE,
                       frames_per_buffer=CHUNK)
    print("✅ Input stream created")
except Exception as e:
    print(f"❌ Input error: {e}")
    exit(1)

try:
    stream_out = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        output=True, output_device_index=OUTPUT_DEVICE,
                        frames_per_buffer=CHUNK)
    print("✅ Output stream created")
except Exception as e:
    print(f"❌ Output error: {e}")
    exit(1)

# Pitch detector
pitch_o = aubio.pitch("yin", CHUNK * 2, CHUNK, RATE)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-40)

# Simple plot
print("📊 Setting up plot...")
fig, ax = plt.subplots()
pitch_history = deque(maxlen=50)
time_history = deque(maxlen=50)
line, = ax.plot([], [])
ax.set_ylim(50, 800)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Pitch (Hz)")
ax.set_title("Your Pitch (Smooth)")
plt.tight_layout()
plt.show(block=False)

print("🎤 Starting smooth karaoke! Sing into your microphone...")
print("💡 You should hear the instrumental + your voice with no lag")
print("📊 You should see a plot of your pitch")
print("🛑 Press Ctrl+C to stop")

start_time = time.time()
frame_count = 0

try:
    while True:
        elapsed = time.time() - start_time
        frame_count += 1
        
        # Read microphone
        data = stream_in.read(CHUNK, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.float32)
        
        # Detect pitch (less frequently to reduce CPU load)
        if frame_count % 8 == 0:  # Only detect pitch every 8th frame
            pitch = pitch_o(samples)[0]
            confidence = pitch_o.get_confidence()
        else:
            pitch = 0
            confidence = 0
        
        # Simple autotune (only when confidence is high)
        if confidence > 0.8 and pitch > 0:
            # Find nearest note frequency
            note_freqs = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]  # C4 to C5
            nearest_note = min(note_freqs, key=lambda x: abs(x - pitch))
            shift_ratio = nearest_note / pitch
            tuned_samples = resample(samples, int(len(samples) * shift_ratio))
            if len(tuned_samples) < CHUNK:
                tuned_samples = np.pad(tuned_samples, (0, CHUNK - len(tuned_samples)))
            else:
                tuned_samples = tuned_samples[:CHUNK]
        else:
            tuned_samples = samples
        
        # Get instrumental chunk (preloaded in memory)
        instrumental = get_instrumental_chunk()
        
        # Mix with instrumental (more instrumental, less voice for better balance)
        mix = 0.7 * instrumental + 0.3 * tuned_samples
        mix = np.clip(mix, -1.0, 1.0)
        
        # Output
        stream_out.write(mix.astype(np.float32).tobytes())
        
        # Update plot (less frequently to reduce overhead)
        if frame_count % 40 == 0:
            time_history.append(elapsed)
            pitch_history.append(pitch)
            
            if len(time_history) > 1:
                line.set_data(list(time_history), list(pitch_history))
                ax.set_xlim(max(0, elapsed - 5), elapsed + 0.5)
                plt.pause(0.001)
        
        # Debug output (less frequent)
        if frame_count % 400 == 0:
            print(f"⏱️  {elapsed:.1f}s | 🎤 Pitch: {pitch:.1f}Hz | Confidence: {confidence:.2f}")

except KeyboardInterrupt:
    print("\n🛑 Stopping karaoke...")

finally:
    stream_in.stop_stream()
    stream_out.stop_stream()
    stream_in.close()
    stream_out.close()
    p.terminate()
    print("✅ Cleanup complete!") 