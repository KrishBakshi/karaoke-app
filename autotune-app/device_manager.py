#!/usr/bin/env python3
"""
Audio Device Manager for Karaoke System
Lists available devices and helps select them for the C++ backend
"""

import subprocess
import sys
import json
import os

def get_audio_devices():
    """Get list of available audio devices using pactl"""
    try:
        # Get input devices (microphones)
        result = subprocess.run(['pactl', 'list', 'sources', 'short'], 
                              capture_output=True, text=True, check=True)
        input_devices = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    device_id = parts[0]
                    device_name = parts[1]
                    input_devices.append({'id': device_id, 'name': device_name})
        
        # Get output devices (speakers/headphones)
        result = subprocess.run(['pactl', 'list', 'sinks', 'short'], 
                              capture_output=True, text=True, check=True)
        output_devices = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    device_id = parts[0]
                    device_name = parts[1]
                    output_devices.append({'id': device_id, 'name': device_name})
        
        return input_devices, output_devices
    except subprocess.CalledProcessError:
        print("❌ Error: Could not get audio devices. Make sure PulseAudio is running.")
        return [], []
    except FileNotFoundError:
        print("❌ Error: 'pactl' command not found. Install PulseAudio utilities.")
        return [], []

def list_devices():
    """List all available audio devices"""
    input_devices, output_devices = get_audio_devices()
    
    print("🎤 Available Audio Input Devices (Microphones):")
    for device in input_devices:
        print(f"   [{device['id']}] {device['name']}")
    
    print("\n🔊 Available Audio Output Devices (Speakers/Headphones):")
    for device in output_devices:
        print(f"   [{device['id']}] {device['name']}")
    
    return input_devices, output_devices

def select_devices():
    """Interactive device selection"""
    input_devices, output_devices = get_audio_devices()
    
    if not input_devices or not output_devices:
        print("❌ No audio devices found!")
        return None, None
    
    print("\n🎤 Select Input Device (Microphone):")
    for i, device in enumerate(input_devices):
        print(f"   {i+1}. {device['name']}")
    
    try:
        choice = int(input(f"Enter choice (1-{len(input_devices)}): ")) - 1
        if 0 <= choice < len(input_devices):
            selected_input = input_devices[choice]['name']
        else:
            print("❌ Invalid choice, using first device")
            selected_input = input_devices[0]['name']
    except ValueError:
        print("❌ Invalid input, using first device")
        selected_input = input_devices[0]['name']
    
    print("\n🔊 Select Output Device (Speakers/Headphones):")
    for i, device in enumerate(output_devices):
        print(f"   {i+1}. {device['name']}")
    
    try:
        choice = int(input(f"Enter choice (1-{len(output_devices)}): ")) - 1
        if 0 <= choice < len(output_devices):
            selected_output = output_devices[choice]['name']
        else:
            print("❌ Invalid choice, using first device")
            selected_output = output_devices[0]['name']
    except ValueError:
        print("❌ Invalid input, using first device")
        selected_output = output_devices[0]['name']
    
    return selected_input, selected_output

def run_karaoke_with_devices(song_name, input_device=None, output_device=None):
    """Run the C++ karaoke program with selected devices"""
    cmd = ['./karaoke', song_name]
    
    if input_device and output_device:
        cmd.extend([input_device, output_device])
        print(f"🎵 Running karaoke with devices:")
        print(f"   🎤 Input: {input_device}")
        print(f"   🔊 Output: {output_device}")
    else:
        print(f"🎵 Running karaoke with auto-device selection")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running karaoke: {e}")
    except FileNotFoundError:
        print("❌ Error: 'karaoke' executable not found. Make sure to compile the C++ program first.")

def main():
    if len(sys.argv) < 2:
        print("🎵 Audio Device Manager for Karaoke System")
        print("Usage:")
        print("  python3 device_manager.py --list                    # List all devices")
        print("  python3 device_manager.py --select                  # Interactive device selection")
        print("  python3 device_manager.py <song_name>              # Run with auto-device selection")
        print("  python3 device_manager.py <song_name> --select     # Run with device selection")
        print("  python3 device_manager.py <song_name> <input> <output>  # Run with specific devices")
        print("\nExamples:")
        print("  python3 device_manager.py --list")
        print("  python3 device_manager.py Taylor_Swift_-_Love_Story --select")
        print("  python3 device_manager.py MySong \"USB Microphone\" \"USB Headphones\"")
        return
    
    if sys.argv[1] == '--list':
        list_devices()
        return
    
    if sys.argv[1] == '--select':
        input_device, output_device = select_devices()
        if input_device and output_device:
            print(f"\n✅ Selected devices:")
            print(f"   🎤 Input: {input_device}")
            print(f"   🔊 Output: {output_device}")
        return
    
    song_name = sys.argv[1]
    
    if len(sys.argv) == 4:
        # Specific devices provided
        input_device = sys.argv[2]
        output_device = sys.argv[3]
        run_karaoke_with_devices(song_name, input_device, output_device)
    elif len(sys.argv) == 2:
        if '--select' in sys.argv:
            # Interactive selection
            input_device, output_device = select_devices()
            if input_device and output_device:
                run_karaoke_with_devices(song_name, input_device, output_device)
        else:
            # Auto-device selection
            run_karaoke_with_devices(song_name)
    else:
        print("❌ Invalid arguments. Use --help for usage information.")

if __name__ == "__main__":
    main()
