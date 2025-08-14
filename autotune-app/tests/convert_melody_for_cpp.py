# convert_melody_for_cpp.py
# Converts the continuous melody map to a C++ header file

import numpy as np

print("🔄 Converting melody map to C++ format...")

# Load the continuous melody map
data = np.load('blinding_lights_melody_map_continuous.npz')
times = data['times']
freqs = data['freqs']

print(f"📊 Loaded {len(times)} melody points")

# Create C++ header file
header_content = f"""// Auto-generated melody map header
// Generated from blinding_lights_melody_map_continuous.npz
// Contains {len(times)} melody points from {times[0]:.2f}s to {times[-1]:.2f}s

#ifndef MELODY_MAP_H
#define MELODY_MAP_H

#include <vector>
#include <utility>

// Melody map data: (time, frequency) pairs
const std::vector<std::pair<float, float>> MELODY_MAP = {{
"""

# Add melody points
for i, (t, f) in enumerate(zip(times, freqs)):
    if i % 100 == 0:  # Add newlines every 100 points for readability
        header_content += "\n    "
    header_content += f"{{{t:.3f}f, {f:.3f}f}}"
    if i < len(times) - 1:
        header_content += ", "

header_content += """
};

#endif // MELODY_MAP_H
"""

# Write header file
with open('melody_map.h', 'w') as f:
    f.write(header_content)

print(f"✅ Created melody_map.h with {len(times)} melody points")
print(f"📁 File: melody_map.h")
print(f"🎯 Now you can #include \"melody_map.h\" in your C++ code!")
print(f"💡 Use MELODY_MAP instead of creating dummy melody data")

# Also create a simple text file for easy inspection
with open('melody_map.txt', 'w') as f:
    f.write(f"# Melody Map: {len(times)} points\n")
    f.write(f"# Format: time(s), frequency(Hz)\n")
    f.write(f"# Range: {times[0]:.2f}s to {times[-1]:.2f}s\n\n")
    for t, f in zip(times, freqs):
        f.write(f"{t:.3f}, {f:.3f}\n")

print(f"📝 Also created melody_map.txt for easy inspection")
