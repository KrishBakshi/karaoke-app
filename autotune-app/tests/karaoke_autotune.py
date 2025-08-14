# karaoke_autotune.py (FLAC-compatible)

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

# ==== LOAD MELODY MAP ====
melody_data = np.load("blinding_lights_melody_map_continuous.npz")
melody_times = melody_data["times"]
melody_freqs = melody_data["freqs"]
melody_map = dict(zip(melody_times, melody_freqs))

def get_melody_freq_at(t):
    return melody_map.get(round(t, 2), None)

# ==== LOAD INSTRUMENTAL ====
instr_audio, instr_sr = sf.read(INSTRUMENTAL_PATH, dtype='float32')
instr_pos = 0

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
p = pyaudio.PyAudio()

stream_in = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                   input=True, frames_per_buffer=CHUNK)

stream_out = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    output=True, frames_per_buffer=CHUNK)

# Aubio pitch detector
pitch_o = aubio.pitch("yin", CHUNK * 2, CHUNK, RATE)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-40)

# ==== LIVE PLOT SETUP ====
pitch_history = deque(maxlen=100)
target_history = deque(maxlen=100)
time_axis = deque(maxlen=100)
start_time = time.time()

fig, ax = plt.subplots()
line1, = ax.plot([], [], label="🎤 Your Pitch")
line2, = ax.plot([], [], label="🎼 Target Pitch")
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

ani = FuncAnimation(fig, update_plot, interval=100)
plt.show(block=False)

# ==== REAL-TIME LOOP ====
print("🎤 Karaoke Started! Sing along... (Ctrl+C to stop)")
try:
    while True:
        elapsed = time.time() - start_time

        # 1. Read mic input
        data = stream_in.read(CHUNK, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.float32)

        # 2. Detect pitch
        pitch = pitch_o(samples)[0]
        confidence = pitch_o.get_confidence()

        # 3. Get target melody pitch
        target_pitch = get_melody_freq_at(elapsed)
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
