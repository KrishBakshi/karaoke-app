import pyaudio
import numpy as np
import time
import soundfile as sf
from scipy.signal import resample
import matplotlib.pyplot as plt
from collections import deque
import aubio
import wave
import os

print("🎤 Voice-Focused Karaoke with Recording")

# Configuration
CHUNK = 1024
RATE = 48000
FORMAT = pyaudio.paFloat32
CHANNELS = 1
INPUT_DEVICE = 0  # EarPods for microphone
OUTPUT_DEVICE = 2  # HD-Audio Generic: ALC256 Analog for speakers

# Recording setup
RECORDING_PATH = "karaoke_voice_focused.wav"
RECORDING_DURATION = 300  # 5 minutes max

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
print(f"🎤 Using input device {INPUT_DEVICE} (EarPods)")
print(f"🔊 Using output device {OUTPUT_DEVICE} (Laptop speakers)")
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

# Setup recording
print("📹 Setting up recording...")
recording_frames = []
recording_start_time = time.time()

# Pitch detector with actual sample rate (more sensitive for low voice levels)
print("🎵 Setting up pitch detector...")
pitch_o = aubio.pitch("yin", CHUNK * 2, CHUNK, actual_rate)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-60)  # Much more sensitive for low voice levels
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
ax.set_title("Voice-Focused Karaoke")
ax.legend()
plt.tight_layout()
plt.show(block=False)

print("🎤 Starting voice-focused karaoke! Sing into your microphone...")
print("💡 Voice will be prominent, background will be quiet")
print("📊 You should see your pitch vs target melody")
print("📹 Recording will be saved to karaoke_voice_focused.wav")
print("🛑 Press Ctrl+C to stop")

start_time = time.time()
frame_count = 0

try:
    while True:
        elapsed = time.time() - start_time
        frame_count += 1
        
        # Check recording duration
        if elapsed > RECORDING_DURATION:
            print(f"⏰ Recording duration limit reached ({RECORDING_DURATION}s)")
            break
        
        # Read microphone
        data = stream_in.read(CHUNK, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.float32)
        
        # Get instrumental chunk (smooth playback)
        instrumental = get_instrumental_chunk()
        
        # Detect pitch (more frequently for better voice capture)
        if frame_count % 4 == 0:
            pitch = pitch_o(samples)[0]
            confidence = pitch_o.get_confidence()
        else:
            pitch = 0
            confidence = 0
        
        # Get target melody frequency
        target_pitch = get_melody_freq_at(elapsed)
        
        # Apply autotune using melody map (much lower threshold for low voice levels)
        if confidence > 0.1 and pitch > 0 and target_pitch is not None:
            # Pitch shift to target melody
            shift_ratio = target_pitch / pitch
            tuned_samples = resample(samples, int(len(samples) * shift_ratio))
            if len(tuned_samples) < CHUNK:
                tuned_samples = np.pad(tuned_samples, (0, CHUNK - len(tuned_samples)))
            else:
                tuned_samples = tuned_samples[:CHUNK]
        else:
            tuned_samples = samples
        
        # Mix with instrumental (VOICE PROMINENT, background very quiet)
        mix = 0.1 * instrumental + 0.8 * tuned_samples
        mix = np.clip(mix, -1.0, 1.0)
        
        # Output
        stream_out.write(mix.astype(np.float32).tobytes())
        
        # Record the mixed audio
        recording_frames.append(mix.astype(np.float32).tobytes())
        
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
    # Save recording
    if recording_frames:
        print("💾 Saving recording...")
        with wave.open(RECORDING_PATH, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(actual_rate)
            wf.writeframes(b''.join(recording_frames))
        print(f"✅ Recording saved to {RECORDING_PATH}")
    
    stream_in.stop_stream()
    stream_out.stop_stream()
    stream_in.close()
    stream_out.close()
    p.terminate()
    print("✅ Cleanup complete!") 