import pyaudio
import numpy as np
import time
import soundfile as sf
from scipy.signal import resample
import matplotlib.pyplot as plt
from collections import deque
import aubio

print("🎵 Low-Latency Karaoke System")

# Configuration - Smaller buffers for lower latency
CHUNK = 256  # Reduced from 1024 for lower latency
RATE = 48000
FORMAT = pyaudio.paFloat32
CHANNELS = 1
INPUT_DEVICE = 6   # EarPods: USB Audio
OUTPUT_DEVICE = 6  # EarPods: USB Audio

# Load instrumental
print("🎼 Loading instrumental...")
try:
    instr_audio, instr_sr = sf.read("./The_Weeknd_-_Blinding_Lights_O_separated/The Weeknd - Blinding Lights (Instrumental model_bs_roformer_ep_317_sdr_1).FLAC", dtype='float32')
    print(f"✅ Loaded {len(instr_audio)} samples at {instr_sr}Hz")
    
    # Resample to 48kHz if needed
    if instr_sr != RATE:
        print(f"🔄 Resampling from {instr_sr}Hz to {RATE}Hz...")
        instr_audio = resample(instr_audio, int(len(instr_audio) * RATE / instr_sr))
        print(f"✅ Resampled to {len(instr_audio)} samples")
    
    instr_pos = 0
except Exception as e:
    print(f"❌ Error loading instrumental: {e}")
    exit(1)

def get_instrumental_chunk():
    global instr_pos
    chunk = instr_audio[instr_pos:instr_pos + CHUNK]
    instr_pos += CHUNK
    
    if len(chunk) < CHUNK:
        instr_pos = 0
        chunk = np.pad(chunk, (0, CHUNK - len(chunk)))
    
    if len(chunk.shape) > 1:
        chunk = chunk[:, 0]
    
    return chunk

# Setup audio with low latency
print("🔊 Setting up low-latency audio...")
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

# Pitch detector with smaller buffer
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
ax.set_title("Your Pitch (Low Latency)")
plt.tight_layout()
plt.show(block=False)

print("🎤 Starting low-latency karaoke! Sing into your microphone...")
print("💡 You should hear the instrumental + your voice with minimal delay")
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
        
        # Detect pitch (only every few frames to reduce CPU load)
        if frame_count % 4 == 0:  # Only detect pitch every 4th frame
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
        
        # Mix with instrumental (reduced instrumental volume)
        instrumental = get_instrumental_chunk()
        mix = 0.5 * instrumental + 0.5 * tuned_samples  # More balanced mix
        mix = np.clip(mix, -1.0, 1.0)
        
        # Output
        stream_out.write(mix.astype(np.float32).tobytes())
        
        # Update plot (less frequently to reduce overhead)
        if frame_count % 20 == 0:
            time_history.append(elapsed)
            pitch_history.append(pitch)
            
            if len(time_history) > 1:
                line.set_data(list(time_history), list(pitch_history))
                ax.set_xlim(max(0, elapsed - 5), elapsed + 0.5)
                plt.pause(0.001)  # Shorter pause
        
        # Debug output (less frequent)
        if frame_count % 200 == 0:
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