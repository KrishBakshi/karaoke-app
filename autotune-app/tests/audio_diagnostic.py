# audio_diagnostic.py
import pyaudio
import numpy as np
import wave
import soundfile as sf
import time

CHUNK = 1024
RATE = 44100
CHANNELS = 1

p = pyaudio.PyAudio()


def list_audio_devices():
    print("\n🔎 Available Audio Devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        io_type = []
        if info['maxInputChannels'] > 0:
            io_type.append("Input")
        if info['maxOutputChannels'] > 0:
            io_type.append("Output")
        print(f"[{i}] {info['name']} ({', '.join(io_type)})")


def test_speaker_output():
    print("\n🔊 Testing speaker output (440 Hz tone for 2 seconds)...")
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=RATE,
                    output=True)

    t = np.linspace(0, 2, RATE * 2)
    tone = 0.3 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    stream.write(tone.tobytes())

    stream.stop_stream()
    stream.close()
    print("✅ Tone played (if you heard it, speaker is working)")


def test_mic_input():
    print("\n🎙️ Testing mic input (recording 3 seconds)...")
    FORMAT = pyaudio.paInt16
    RECORD_SECONDS = 3
    OUTPUT_FILE = "mic_test.wav"

    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

    frames = [stream.read(CHUNK) for _ in range(int(RATE / CHUNK * RECORD_SECONDS))]

    stream.stop_stream()
    stream.close()

    with wave.open(OUTPUT_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print(f"✅ Saved recording to {OUTPUT_FILE} — play it with VLC or Audacity to check")


def test_flac_playback():
    print("\n🎧 Testing FLAC playback...")
    flac_path = input("Enter full path to FLAC file (or drag & drop here): ").strip().strip('"')

    try:
        data, sr = sf.read(flac_path, dtype='float32')
        if len(data.shape) > 1:
            data = data[:, 0]

        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=sr, output=True)
        print("▶️ Playing...")
        stream.write(data.tobytes())
        stream.stop_stream()
        stream.close()
        print("✅ FLAC playback complete (if you heard it, instrumental is working)")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("\n🎧 AUDIO DIAGNOSTIC TOOL\n")
    list_audio_devices()
    test_speaker_output()
    test_mic_input()
    test_flac_playback()
    p.terminate()
    print("\n✅ All tests completed. Use the results to configure your karaoke script accordingly.")


if __name__ == "__main__":
    main()
