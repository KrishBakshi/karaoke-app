"""
Simple wrapper script to run the C++ karaoke program with automatic song detection.
This script finds the correct file paths and runs the karaoke program.
"""

import sys
import subprocess
from song_finder import find_song_files

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h', 'help']:
        print("🎵 Karaoke Runner")
        print("📖 Usage: python3 run_karaoke.py <song_name>")
        print("\n💡 Examples:")
        print("   python3 run_karaoke.py Taylor_Swift_-_Love_Story")
        print("\n🔍 To see available songs: python3 song_finder.py --list")
        print("Usage: python3 run_karaoke.py <song_name> [--autotune 0.8] [--pitch-shift 2] [--voice-volume 1.2] [--instrument-volume 2.0]")
        return
    
    song_input = sys.argv[1]
    
    # Parse voice effect parameters
    voice_params = {
        'autotune_strength': 1.0,    # Default: full autotune
        'pitch_shift': 0.0,          # Default: no pitch shift
        'voice_volume': 1.1,         # Default: slight boost
        'instrument_volume': 2.0,    # Default: instrumental volume (was hardcoded 2.0f)
        'enable_chorus': False,      # Default: no chorus
        'chorus_depth': 0.1,         # Default: subtle chorus
        'enable_reverb': False,      # Default: no reverb
        'reverb_wetness': 0.3        # Default: moderate reverb
    }

        # Parse command line arguments for voice effects
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--autotune' and i + 1 < len(sys.argv):
            voice_params['autotune_strength'] = float(sys.argv[i + 1])
            i += 2
        elif arg == '--pitch-shift' and i + 1 < len(sys.argv):
            voice_params['pitch_shift'] = float(sys.argv[i + 1])
            i += 2
        elif arg == '--voice-volume' and i + 1 < len(sys.argv):
            voice_params['voice_volume'] = float(sys.argv[i + 1])
            i += 2
        elif arg == '--instrument-volume' and i + 1 < len(sys.argv):
            voice_params['instrument_volume'] = float(sys.argv[i + 1])
            i += 2
        elif arg == '--enable-chorus' and i + 1 < len(sys.argv):
            voice_params['enable_chorus'] = (sys.argv[i + 1] == '1')
            i += 2
        elif arg == '--chorus-depth' and i + 1 < len(sys.argv):
            voice_params['chorus_depth'] = float(sys.argv[i + 1])
            i += 2
        elif arg == '--enable-reverb' and i + 1 < len(sys.argv):
            voice_params['enable_reverb'] = (sys.argv[i + 1] == '1')
            i += 2
        elif arg == '--reverb-wetness' and i + 1 < len(sys.argv):
            voice_params['reverb_wetness'] = float(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    # Print voice effect parameters
    print("\n🎤 Voice Effect Parameters:")
    print(f"  Autotune Strength: {voice_params['autotune_strength']}")
    print(f"  Pitch Shift: {voice_params['pitch_shift']} semitones")
    print(f"  Voice Volume: {voice_params['voice_volume']}")
    print(f"  Instrument Volume: {voice_params['instrument_volume']}")
    print(f"  Chorus: {'Enabled' if voice_params['enable_chorus'] else 'Disabled'}")
    print(f"  Chorus Depth: {voice_params['chorus_depth']}")
    print(f"  Reverb: {'Enabled' if voice_params['enable_reverb'] else 'Disabled'}")
    print(f"  Reverb Wetness: {voice_params['reverb_wetness']}")
    
    print(f"🎵 Looking for song: {song_input}")
    melody_file, instrumental_file, message = find_song_files(song_input)
    
    if not melody_file or not instrumental_file:
        print(message)
        return
    
    print(message)
    print(f"\n🚀 Starting karaoke with song: {song_input}")
    print("=" * 60)
    
    try:
        # Run the C++ karaoke program with song name first, then file paths
        result = subprocess.run([
                "./autotune-karaoke", 
                song_input, 
                melody_file, 
                instrumental_file,
                str(voice_params['autotune_strength']),
                str(voice_params['pitch_shift']),
                str(voice_params['voice_volume']),
                str(voice_params['instrument_volume']),
                str(voice_params['enable_chorus']),
                str(voice_params['chorus_depth']),
                str(voice_params['enable_reverb']),
                str(voice_params['reverb_wetness'])
            ], check=True)        
        print("\n✅ Karaoke session completed!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Karaoke program failed with exit code: {e.returncode}")
    except FileNotFoundError:
        print("\n❌ Karaoke executable not found! Make sure to compile the C++ program first.")
        print("💡 Run: make clean && make")
    except KeyboardInterrupt:
        print("\n\n🛑 Karaoke session interrupted by user.")

if __name__ == "__main__":
    main()
