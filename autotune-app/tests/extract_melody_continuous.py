# extract_melody_continuous.py
# Creates a continuous melody map by filling gaps for smooth visualization

import librosa
import numpy as np
from scipy.interpolate import interp1d

VOCAL_PATH = "./The_Weeknd_-_Blinding_Lights_O_separated/stems/The Weeknd - Blinding Lights (Lead Vocals mel_band_roformer_karaoke_aufr).FLAC"
OUTPUT_PATH = "blinding_lights_melody_map_continuous.npz"

print("🔍 Extracting continuous melody from:", VOCAL_PATH)
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

# Extract times and frequencies
extracted_times = np.array([t for t, f in melody_map])
extracted_freqs = np.array([f for t, f in melody_map])

print(f"📊 Original extraction: {len(melody_map)} melody points")
print(f"⏱️  Time range: {extracted_times.min():.2f}s to {extracted_times.max():.2f}s")

# Create continuous time array (every 0.1 seconds)
continuous_times = np.arange(0, extracted_times.max() + 0.1, 0.1)
print(f"🔄 Creating continuous timeline: {len(continuous_times)} points (every 0.1s)")

# Interpolate frequencies to fill gaps
if len(extracted_times) > 1:
    # Create interpolation function
    interp_func = interp1d(extracted_times, extracted_freqs, 
                           kind='linear', bounds_error=False, fill_value='extrapolate')
    
    # Interpolate to continuous timeline
    continuous_freqs = interp_func(continuous_times)
    
    # Fill any remaining NaN values with the last known frequency
    last_valid_freq = None
    for i in range(len(continuous_freqs)):
        if np.isnan(continuous_freqs[i]) or continuous_freqs[i] <= 0:
            if last_valid_freq is not None:
                continuous_freqs[i] = last_valid_freq
            else:
                # If no previous frequency, use a default (middle C)
                continuous_freqs[i] = 261.63
        else:
            last_valid_freq = continuous_freqs[i]
    
    print(f"✅ Interpolation complete: {len(continuous_freqs)} continuous frequency points")
    
    # Check for any remaining gaps
    gaps = np.diff(continuous_times)
    print(f"🔍 Time resolution: {gaps[0]:.3f}s between points")
    print(f"📈 Frequency range: {continuous_freqs.min():.1f}Hz to {continuous_freqs.max():.1f}Hz")
    
else:
    print("❌ Not enough data points for interpolation!")
    exit(1)

# Save continuous melody map
np.savez_compressed(OUTPUT_PATH,
    times=continuous_times,
    freqs=continuous_freqs
)

print(f"💾 Saved continuous melody map to: {OUTPUT_PATH}")
print(f"🎯 Now you'll have smooth, continuous red lines in your visualization!")

# Verify the output
print("\n🔍 Verification:")
data = np.load(OUTPUT_PATH)
print(f"   Times: {data['times'].shape[0]} points")
print(f"   Freqs: {data['freqs'].shape[0]} points")
print(f"   Time gaps: {np.diff(data['times'])[:5]}... (should all be 0.1)")
print(f"   No NaN values: {not np.any(np.isnan(data['freqs']))}")
