import soundfile as sf
import numpy as np
import pyaudio
import time

print("🎵 Playing Karaoke Recording...")

# Load the recording
try:
    data, sr = sf.read('karaoke_output.wav')
    print(f"✅ Loaded recording: {len(data)/sr:.1f}s at {sr}Hz")
    print(f"📊 Audio levels: {np.min(data):.3f} to {np.max(data):.3f}")
    
    # Normalize audio
    if np.max(np.abs(data)) > 0:
        data = data / np.max(np.abs(data)) * 0.8  # Normalize to 80%
    
    # Convert to int16 for playback
    data_int16 = (data * 32767).astype(np.int16)
    
    # Setup audio playback
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sr,
                    output=True)
    
    print("🔊 Playing recording... (Press Ctrl+C to stop)")
    
    # Play in chunks
    chunk_size = 1024
    for i in range(0, len(data_int16), chunk_size):
        chunk = data_int16[i:i+chunk_size]
        if len(chunk) < chunk_size:
            # Pad with zeros if needed
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
        stream.write(chunk.tobytes())
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("✅ Playback complete!")
    
except Exception as e:
    print(f"❌ Error playing recording: {e}") 