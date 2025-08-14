import pyaudio
import numpy as np
import time
import soundfile as sf
from scipy.signal import resample
import matplotlib.pyplot as plt
from collections import deque
import aubio

print("🎵 Separate Background Karaoke (No Lag)")

# Configuration
CHUNK = 2048  # Larger buffer for smoother background
RATE = 48000
FORMAT = pyaudio.paFloat32
CHANNELS = 1
INPUT_DEVICE = 6   # EarPods: USB Audio
OUTPUT_DEVICE = 6  # EarPods: USB Audio

# Load melody map
print("🎼 Loading melody map...")
try:
    melody_data = np.load("blinding_lights_melody_map.npz")
    melody_times = melody_data["times"]
    melody_freqs = melody_data["freqs"]
    melody_map = dict(zip(melody_times, melody_freqs))
    print(f"✅ Loaded {len(melody_map)} melody points")
except Exception as e:
    print(f"❌ Error loading melody map: {e}")
    exit(1)

def get_melody_freq_at(t):
    return melody_map.get(round(t, 2), None)

# Load WAV instrumental
print("🎼 Loading WAV instrumental...")
try:
    instr_audio, instr_sr = sf.read("blinding_lights_instrumental.wav", dtype='float32')
    print(f"✅ Loaded {len(instr_audio)} samples at {instr_sr}Hz")
    
    # Ensure it's mono
    if len(instr_audio.shape) > 1:
        instr_audio = instr_audio[:, 0]
    
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

# Plot setup
print("📊 Setting up plot...")
fig, ax = plt.subplots()
pitch_history = deque(maxlen=50)
target_history = deque(maxlen=50)
time_history = deque(maxlen=50)
line1, = ax.plot([], [], label="Your Pitch", color='blue')
line2, = ax.plot([], [], label="Target Melody", color='red')
ax.set_ylim(50, 800)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Pitch (Hz)")
ax.set_title("Separate Background Karaoke")
ax.legend()
plt.tight_layout()
plt.show(block=False)

print("🎤 Starting separate background karaoke! Sing into your microphone...")
print("💡 Background should be smooth, voice will be autotuned to melody")
print("📊 You should see your pitch vs target melody")
print("🛑 Press Ctrl+C to stop")

start_time = time.time()
frame_count = 0

try:
    while True:
        elapsed = time.time() - start_time
        frame_count += 1
        
        # Get instrumental chunk FIRST (priority for smooth playback)
        instrumental = get_instrumental_chunk()
        
        # Read microphone
        data = stream_in.read(CHUNK, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.float32)
        
        # Detect pitch (much less frequently to reduce CPU load)
        if frame_count % 16 == 0:  # Only detect pitch every 16th frame
            pitch = pitch_o(samples)[0]
            confidence = pitch_o.get_confidence()
        else:
            pitch = 0
            confidence = 0
        
        # Get target melody frequency
        target_pitch = get_melody_freq_at(elapsed)
        
        # Apply autotune using melody map (only when confidence is high)
        if confidence > 0.8 and pitch > 0 and target_pitch is not None:
            # Pitch shift to target melody
            shift_ratio = target_pitch / pitch
            tuned_samples = resample(samples, int(len(samples) * shift_ratio))
            if len(tuned_samples) < CHUNK:
                tuned_samples = np.pad(tuned_samples, (0, CHUNK - len(tuned_samples)))
            else:
                tuned_samples = tuned_samples[:CHUNK]
        else:
            tuned_samples = samples
        
        # Mix with instrumental (much more instrumental, less voice processing)
        mix = 0.8 * instrumental + 0.2 * tuned_samples
        mix = np.clip(mix, -1.0, 1.0)
        
        # Output
        stream_out.write(mix.astype(np.float32).tobytes())
        
        # Update plot (much less frequently)
        if frame_count % 40 == 0:
            time_history.append(elapsed)
            pitch_history.append(pitch)
            target_history.append(target_pitch if target_pitch else 0)
            
            if len(time_history) > 1:
                line1.set_data(list(time_history), list(pitch_history))
                line2.set_data(list(time_history), list(target_history))
                ax.set_xlim(max(0, elapsed - 5), elapsed + 0.5)
                plt.pause(0.001)
        
        # Debug output (much less frequent)
        if frame_count % 400 == 0:
            target_str = f"{target_pitch:.1f}Hz" if target_pitch is not None else "None"
            print(f"⏱️  {elapsed:.1f}s | 🎤 Your pitch: {pitch:.1f}Hz | 🎼 Target: {target_str} | Confidence: {confidence:.2f}")

except KeyboardInterrupt:
    print("\n🛑 Stopping karaoke...")

finally:
    stream_in.stop_stream()
    stream_out.stop_stream()
    stream_in.close()
    stream_out.close()
    p.terminate()
    print("✅ Cleanup complete!") 