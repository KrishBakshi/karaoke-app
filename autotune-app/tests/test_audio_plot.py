import numpy as np
import pyaudio
import matplotlib.pyplot as plt
import time

print("🔊 Testing audio playback and plots...")

# Test 1: Simple audio playback
print("🎵 Testing audio playback...")
p = pyaudio.PyAudio()

# Generate a simple sine wave
sample_rate = 44100
duration = 2  # seconds
frequency = 440  # A4 note

t = np.linspace(0, duration, int(sample_rate * duration), False)
sine_wave = 0.3 * np.sin(2 * np.pi * frequency * t)

# Play the sine wave
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=sample_rate,
                output=True,
                output_device_index=5)  # Use device 5

print("🔊 Playing a 440Hz tone for 2 seconds...")
stream.write(sine_wave.astype(np.float32).tobytes())
stream.stop_stream()
stream.close()
p.terminate()
print("✅ Audio test complete!")

# Test 2: Simple plot
print("📊 Testing matplotlib plot...")
fig, ax = plt.subplots()
x = np.linspace(0, 10, 100)
y = np.sin(x)
ax.plot(x, y)
ax.set_title("Test Plot")
ax.set_xlabel("Time")
ax.set_ylabel("Amplitude")
plt.tight_layout()
plt.show(block=False)
print("✅ Plot test complete! You should see a sine wave plot.")

# Test 3: Live plot
print("📈 Testing live plot...")
fig2, ax2 = plt.subplots()
line, = ax2.plot([], [])
ax2.set_xlim(0, 10)
ax2.set_ylim(-1, 1)
ax2.set_title("Live Test Plot")
ax2.set_xlabel("Time")
ax2.set_ylabel("Value")

def update(frame):
    x = np.linspace(0, 10, 100)
    y = np.sin(x + frame * 0.1)
    line.set_data(x, y)
    return line,

from matplotlib.animation import FuncAnimation
ani = FuncAnimation(fig2, update, frames=50, interval=100, cache_frame_data=False)
plt.show(block=False)
print("✅ Live plot test complete! You should see an animated sine wave.")

print("🎯 All tests complete! Check if you:")
print("   1. Heard a 440Hz tone")
print("   2. Saw a static sine wave plot")
print("   3. Saw an animated sine wave plot")

input("Press Enter to continue...") 