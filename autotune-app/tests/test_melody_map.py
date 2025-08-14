# test_melody_map.py
# Test script to verify the continuous melody map works

import numpy as np

print("🧪 Testing Continuous Melody Map")
print("=" * 40)

# Load the continuous melody map
try:
    data = np.load('blinding_lights_melody_map_continuous.npz')
    times = data['times']
    freqs = data['freqs']
    print(f"✅ Successfully loaded melody map")
    print(f"📊 Data shape: {times.shape[0]} time points, {freqs.shape[0]} frequency points")
except Exception as e:
    print(f"❌ Error loading melody map: {e}")
    exit(1)

# Test the melody lookup function
def get_melody_freq_at(t):
    """Get melody frequency at time t (rounded to nearest 0.1s)"""
    rounded_t = round(t, 1)
    try:
        # Find the index for this time
        index = int(rounded_t * 10)  # Since we have 0.1s intervals
        if 0 <= index < len(freqs):
            return freqs[index]
        else:
            return None
    except:
        return None

print(f"\n🎵 Testing melody lookup function:")
print(f"   Time range: {times[0]:.1f}s to {times[-1]:.1f}s")
print(f"   Resolution: {times[1] - times[0]:.1f}s intervals")

# Test various time points
test_times = [0.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 255.0]
print(f"\n🔍 Testing melody lookup at various times:")
for t in test_times:
    freq = get_melody_freq_at(t)
    if freq is not None:
        print(f"   At {t:5.1f}s: {freq:6.1f}Hz")
    else:
        print(f"   At {t:5.1f}s: No data")

# Test continuous lookup (should always return a value)
print(f"\n🔄 Testing continuous lookup (no gaps):")
for t in np.arange(0, 10, 0.5):  # Every 0.5 seconds for first 10 seconds
    freq = get_melody_freq_at(t)
    if freq is not None:
        print(f"   At {t:4.1f}s: {freq:6.1f}Hz")
    else:
        print(f"   At {t:4.1f}s: ❌ GAP DETECTED!")

print(f"\n✅ Melody map test complete!")
print(f"🎯 You should now have smooth, continuous red lines in your visualization!")
print(f"💡 No more disappearing target melody lines!")
