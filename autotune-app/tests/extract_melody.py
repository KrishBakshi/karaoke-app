# extract_melody.py

import librosa
import numpy as np

VOCAL_PATH = "./The_Weeknd_-_Blinding_Lights_O_separated/stems/The Weeknd - Blinding Lights (Lead Vocals mel_band_roformer_karaoke_aufr).FLAC"
OUTPUT_PATH = "blinding_lights_melody_map.npz"

print("🔍 Extracting melody from:", VOCAL_PATH)
y, sr = librosa.load(VOCAL_PATH, sr=44100)

# Use librosa's pyin to extract pitch curve with better parameters
f0, voiced_flag, voiced_probs = librosa.pyin(y,
    fmin=librosa.note_to_hz('C2'),
    fmax=librosa.note_to_hz('C6'),
    sr=sr,
    frame_length=2048,
    hop_length=512,
    fill_na=None)

times = librosa.times_like(f0, sr=sr, hop_length=512)

# Apply smoothing to reduce jitter
f0_smooth = librosa.effects.harmonic(f0, margin=8)

# Filter: Keep only voiced notes with confidence threshold
melody_map = [(round(t, 2), float(f)) for t, f, v, p in zip(times, f0_smooth, voiced_flag, voiced_probs) 
               if v and f is not None and f > 0 and p > 0.5]

# Save to file
np.savez_compressed(OUTPUT_PATH,
    times=[t for t, f in melody_map],
    freqs=[f for t, f in melody_map]
)

print(f"✅ Saved melody map to: {OUTPUT_PATH}")
print(f"📊 Extracted {len(melody_map)} melody points")
