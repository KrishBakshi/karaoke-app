import pyaudio
import numpy as np
import time
import soundfile as sf
from scipy.signal import resample
import matplotlib.pyplot as plt
from collections import deque
import aubio

print("🎵 Simple Karaoke Test System")

# Configuration
CHUNK = 1024
RATE = 44100
FORMAT = pyaudio.paFloat32
CHANNELS = 1
INPUT_DEVICE = 5
OUTPUT_DEVICE = 5

# Load instrumental
print("🎼 Loading instrumental...")
try:
    instr_audio, instr_sr = sf.read("./The_Weeknd_-_Blinding_Lights_O_separated/The Weeknd - Blinding Lights (Instrumental model_bs_roformer_ep_317_sdr_1).FLAC", dtype='float32')
    print(f"✅ Loaded {len(instr_audio)} samples")
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

# Setup audio
print("🔊 Setting up audio...")
p = pyaudio.PyAudio()

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
ax.set_title("Your Pitch")
plt.tight_layout()
plt.show(block=False)

print("🎤 Starting karaoke! Sing into your microphone...")
print("💡 You should hear the instrumental + your voice")
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
        
        # Detect pitch
        pitch = pitch_o(samples)[0]
        confidence = pitch_o.get_confidence()
        
        # Simple autotune (just pitch shift to nearest note)
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
        
        # Mix with instrumental
        instrumental = get_instrumental_chunk()
        mix = 0.7 * instrumental + 0.3 * tuned_samples
        mix = np.clip(mix, -1.0, 1.0)
        
        # Output
        stream_out.write(mix.astype(np.float32).tobytes())
        
        # Update plot
        time_history.append(elapsed)
        pitch_history.append(pitch)
        
        if frame_count % 10 == 0:  # Update plot every 10 frames
            line.set_data(list(time_history), list(pitch_history))
            ax.set_xlim(max(0, elapsed - 5), elapsed + 0.5)
            plt.pause(0.01)
        
        # Debug output
        if frame_count % 100 == 0:
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