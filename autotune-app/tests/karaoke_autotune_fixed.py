# karaoke_autotune_fixed.py (FLAC-compatible)

import pyaudio
import numpy as np
import time
import soundfile as sf
from scipy.signal import resample
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
import aubio

# ==== CONFIG ====
CHUNK = 1024
RATE = 44100
FORMAT = pyaudio.paFloat32
CHANNELS = 1
INSTRUMENTAL_PATH = "./The_Weeknd_-_Blinding_Lights_O_separated/The Weeknd - Blinding Lights (Instrumental model_bs_roformer_ep_317_sdr_1).FLAC"
MELODY_MAP_PATH = "blinding_lights_melody_map.npz"

print("🎵 Starting Karaoke Autotune System...")
print(f"📁 Loading instrumental from: {INSTRUMENTAL_PATH}")
print(f"📁 Loading melody map from: {MELODY_MAP_PATH}")

# Audio device auto-detection function
def find_best_devices():
    p_temp = pyaudio.PyAudio()
    input_device = None
    output_device = None
    
    print("Available audio devices:")
    for i in range(p_temp.get_device_count()):
        info = p_temp.get_device_info_by_index(i)
        print(f"  {i}: {info['name']} (max channels: {info['maxInputChannels']} in, {info['maxOutputChannels']} out)")
        print(f"      Default sample rate: {info['defaultSampleRate']}Hz")
        
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

INPUT_DEVICE, OUTPUT_DEVICE = find_best_devices()

if INPUT_DEVICE is None or OUTPUT_DEVICE is None:
    print("❌ No suitable audio devices found!")
    exit(1)

# ==== LOAD MELODY MAP ====
try:
    melody_data = np.load(MELODY_MAP_PATH)
    melody_times = melody_data["times"]
    melody_freqs = melody_data["freqs"]
    melody_map = dict(zip(melody_times, melody_freqs))
    print(f"✅ Loaded {len(melody_map)} melody points")
except Exception as e:
    print(f"❌ Error loading melody map: {e}")
    exit(1)

def get_melody_freq_at(t):
    return melody_map.get(round(t, 2), None)

# ==== LOAD INSTRUMENTAL ====
try:
    print("🎼 Loading instrumental audio...")
    instr_audio, instr_sr = sf.read(INSTRUMENTAL_PATH, dtype='float32')
    print(f"✅ Loaded instrumental: {len(instr_audio)} samples at {instr_sr}Hz")
    instr_pos = 0
except Exception as e:
    print(f"❌ Error loading instrumental: {e}")
    exit(1)

def read_instrumental_chunk():
    global instr_pos
    chunk = instr_audio[instr_pos:instr_pos + CHUNK]
    instr_pos += CHUNK

    # Loop the audio if it ends
    if len(chunk) < CHUNK:
        instr_pos = 0
        pad = np.zeros(CHUNK - len(chunk), dtype=np.float32)
        chunk = np.concatenate((chunk, pad))

    # If stereo, take only one channel (mono)
    if len(chunk.shape) > 1:
        chunk = chunk[:, 0]

    return chunk

# ==== AUDIO SETUP ====
print("🔊 Setting up audio devices...")
print(f"🎤 Using input device {INPUT_DEVICE}")
print(f"🔊 Using output device {OUTPUT_DEVICE}")
p = pyaudio.PyAudio()

# Try different sample rates if needed
def create_audio_streams():
    rates_to_try = [RATE, 48000, 22050, 16000]  # Try multiple sample rates

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

# Aubio pitch detector with actual sample rate
print("🎵 Setting up pitch detector...")
pitch_o = aubio.pitch("yin", CHUNK * 2, CHUNK, actual_rate)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-40)
print("✅ Pitch detector ready")

# ==== LIVE PLOT SETUP ====
print("📊 Setting up visualization...")
pitch_history = deque(maxlen=100)
target_history = deque(maxlen=100)
time_axis = deque(maxlen=100)
start_time = time.time()

fig, ax = plt.subplots()
line1, = ax.plot([], [], label="Your Pitch")
line2, = ax.plot([], [], label="Target Pitch")
ax.set_ylim(50, 1000)
ax.set_xlim(0, 10)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Frequency (Hz)")
ax.set_title("Live Pitch Tracking")
ax.legend()
plt.tight_layout()

def update_plot(frame):
    times = list(time_axis)
    if not times:
        return line1, line2
    ax.set_xlim(max(0, times[-1] - 10), times[-1] + 0.1)
    line1.set_data(times, list(pitch_history))
    line2.set_data(times, list(target_history))
    return line1, line2

ani = FuncAnimation(fig, update_plot, interval=100, cache_frame_data=False)
plt.show(block=False)
print("✅ Visualization ready")

# ==== REAL-TIME LOOP ====
print("🎤 Karaoke Started! Sing along... (Ctrl+C to stop)")
print("💡 Make sure your microphone is not muted and volume is up!")
print("🎵 You should hear the instrumental backing track and your autotuned voice!")

try:
    frame_count = 0
    while True:
        elapsed = time.time() - start_time
        frame_count += 1

        # 1. Read mic input
        data = stream_in.read(CHUNK, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.float32)

        # 2. Detect pitch
        pitch = pitch_o(samples)[0]
        confidence = pitch_o.get_confidence()

        # 3. Get target melody pitch
        target_pitch = get_melody_freq_at(elapsed)
        
        # Debug output every 100 frames (about every 2 seconds)
        if frame_count % 100 == 0:
            target_str = f"{target_pitch:.1f}Hz" if target_pitch is not None else "None"
            print(f"⏱️  Time: {elapsed:.1f}s | 🎤 Your pitch: {pitch:.1f}Hz | 🎼 Target: {target_str} | Confidence: {confidence:.2f}")

        if confidence < 0.8 or pitch <= 0 or target_pitch is None:
            tuned_samples = samples
        else:
            shift_ratio = target_pitch / pitch
            resampled = resample(samples, int(len(samples) * shift_ratio))
            if len(resampled) < CHUNK:
                resampled = np.pad(resampled, (0, CHUNK - len(resampled)))
            else:
                resampled = resampled[:CHUNK]
            tuned_samples = resampled

        # 4. Mix with instrumental
        instrumental = read_instrumental_chunk()
        mix = 0.5 * tuned_samples + 0.5 * instrumental
        mix = np.clip(mix, -1.0, 1.0)

        # 5. Output
        stream_out.write(mix.astype(np.float32).tobytes())

        # 6. Update plot
        time_axis.append(elapsed)
        pitch_history.append(pitch)
        target_history.append(target_pitch if target_pitch else 0)

except KeyboardInterrupt:
    print("\n🛑 Karaoke ended.")
    stream_in.stop_stream()
    stream_out.stop_stream()
    stream_in.close()
    stream_out.close()
    p.terminate()
except Exception as e:
    print(f"❌ Error during processing: {e}")
    stream_in.stop_stream()
    stream_out.stop_stream()
    stream_in.close()
    stream_out.close()
    p.terminate() 