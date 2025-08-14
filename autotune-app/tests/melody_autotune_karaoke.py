import pyaudio
import numpy as np
import time
import soundfile as sf
from scipy.signal import resample
import matplotlib.pyplot as plt
from collections import deque
import aubio

print("🎵 Melody Map Autotune Karaoke")

# Configuration
CHUNK = 1024
RATE = 48000
FORMAT = pyaudio.paFloat32
CHANNELS = 1
# Auto-detect audio devices
def find_audio_devices():
    p_temp = pyaudio.PyAudio()
    input_device = None
    output_device = None
    
    print("Available audio devices:")
    for i in range(p_temp.get_device_count()):
        info = p_temp.get_device_info_by_index(i)
        print(f"  {i}: {info['name']} (max channels: {info['maxInputChannels']} in, {info['maxOutputChannels']} out)")
        
        # Prefer laptop mic/speakers for better compatibility
        if "ALC256 Analog" in info['name'] and info['maxInputChannels'] > 0:
            input_device = i
        # Fallback to EarPods for input if no laptop mic
        elif input_device is None and "EarPods" in info['name'] and info['maxInputChannels'] > 0:
            input_device = i
        
        # Prefer laptop speakers for output
        if "ALC256 Analog" in info['name'] and info['maxOutputChannels'] > 0:
            output_device = i
        # Fallback to EarPods for output
        elif output_device is None and "EarPods" in info['name'] and info['maxOutputChannels'] > 0:
            output_device = i
    
    p_temp.terminate()
    return input_device, output_device

# Use available devices - EarPods for input, laptop speakers for output
INPUT_DEVICE = 0  # EarPods for microphone
OUTPUT_DEVICE = 2  # HD-Audio Generic: ALC256 Analog for speakers

print(f"🎤 Using input device {INPUT_DEVICE} (EarPods)")
print(f"🔊 Using output device {OUTPUT_DEVICE} (Laptop speakers)")

# Load melody map
print("🎼 Loading melody map...")
try:
    melody_data = np.load("blinding_lights_melody_map_continuous.npz")
    melody_times = melody_data["times"]
    melody_freqs = melody_data["freqs"]
    melody_map = dict(zip(melody_times, melody_freqs))
    print(f"✅ Loaded {len(melody_map)} continuous melody points (no gaps!)")
except Exception as e:
    print(f"❌ Error loading melody map: {e}")
    exit(1)

def get_melody_freq_at(t):
    return melody_map.get(round(t, 2), None)

# Load separated instrumental
INSTRUMENTAL_PATH = "./The_Weeknd_-_Blinding_Lights_O_separated/The Weeknd - Blinding Lights (Instrumental model_bs_roformer_ep_317_sdr_1).FLAC"
print("🎼 Loading separated instrumental...")
try:
    instr_audio, instr_sr = sf.read(INSTRUMENTAL_PATH, dtype='float32')
    print(f"✅ Loaded {len(instr_audio)} samples at {instr_sr}Hz")
    
    # Ensure it's mono
    if len(instr_audio.shape) > 1:
        instr_audio = instr_audio[:, 0]
    
    instr_pos = 0
    print("✅ Audio preloaded into memory")
except Exception as e:
    print(f"❌ Error loading instrumental: {e}")
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
print(f"🎤 Using input device {INPUT_DEVICE}")
print(f"🔊 Using output device {OUTPUT_DEVICE}")
print(f"⚡ Buffer size: {CHUNK} samples ({CHUNK/RATE*1000:.1f}ms latency)")

p = pyaudio.PyAudio()

# Try different sample rates if needed
def create_audio_streams():
    rates_to_try = [RATE, 44100, 22050, 16000]  # Try multiple sample rates
    
    for rate in rates_to_try:
        try:
            print(f"Trying sample rate: {rate}Hz")
            stream_in = p.open(format=FORMAT, channels=CHANNELS, rate=rate,
                       input=True, input_device_index=INPUT_DEVICE,
                       frames_per_buffer=CHUNK)
            print(f"✅ Input stream created successfully at {rate}Hz")

            stream_out = p.open(format=FORMAT, channels=CHANNELS, rate=rate,
                        output=True, output_device_index=OUTPUT_DEVICE,
                        frames_per_buffer=CHUNK)
            print(f"✅ Output stream created successfully at {rate}Hz")
            
            return stream_in, stream_out, rate
            
        except Exception as e:
            print(f"❌ Error at {rate}Hz: {e}")
            continue
    
    print("❌ Could not create audio streams with any sample rate!")
    exit(1)

stream_in, stream_out, actual_rate = create_audio_streams()

# Pitch detector with actual sample rate
print("🎵 Setting up pitch detector...")
pitch_o = aubio.pitch("yin", CHUNK * 2, CHUNK, actual_rate)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-40)
print("✅ Pitch detector ready")

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
ax.set_title("Melody Map Autotune")
ax.legend()
plt.tight_layout()
plt.show(block=False)

print("🎤 Starting melody map karaoke! Sing into your microphone...")
print("💡 Instrumental should play smoothly, voice will be autotuned to melody")
print("📊 You should see your pitch vs target melody")
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
        
        # Get instrumental chunk (smooth playback)
        instrumental = get_instrumental_chunk()
        
        # Detect pitch (less frequently)
        if frame_count % 8 == 0:
            pitch = pitch_o(samples)[0]
            confidence = pitch_o.get_confidence()
        else:
            pitch = 0
            confidence = 0
        
        # Get target melody frequency
        target_pitch = get_melody_freq_at(elapsed)
        
        # Apply autotune using melody map
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
        
        # Mix with instrumental (prioritize instrumental)
        mix = 0.7 * instrumental + 0.3 * tuned_samples
        mix = np.clip(mix, -1.0, 1.0)
        
        # Output
        stream_out.write(mix.astype(np.float32).tobytes())
        
        # Update plot
        if frame_count % 20 == 0:
            time_history.append(elapsed)
            pitch_history.append(pitch)
            target_history.append(target_pitch if target_pitch else 0)
            
            if len(time_history) > 1:
                line1.set_data(list(time_history), list(pitch_history))
                line2.set_data(list(time_history), list(target_history))
                ax.set_xlim(max(0, elapsed - 5), elapsed + 0.5)
                plt.pause(0.001)
        
        # Debug output
        if frame_count % 200 == 0:
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