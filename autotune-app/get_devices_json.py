#!/usr/bin/env python3
"""
Get audio devices in JSON format for frontend integration
"""

import subprocess
import json
import sys

def get_audio_devices():
    """Get list of available audio devices using device_list utility"""
    try:
        # Try to find device_list in the same directory as this script
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        device_list_path = os.path.join(script_dir, 'device_list')
        
        # Check if device_list exists
        if not os.path.exists(device_list_path):
            print(f"Error: device_list executable not found at {device_list_path}", file=sys.stderr)
            print("Make sure to compile it first with: make all", file=sys.stderr)
            return {'inputs': [], 'outputs': []}
        
        result = subprocess.run([device_list_path], 
                              capture_output=True, text=True, check=True)
        
        input_devices = []
        output_devices = []
        
        lines = result.stdout.split('\n')
        in_input_section = False
        in_output_section = False
        
        for line in lines:
            if '🎤 Input Devices (Microphones):' in line:
                in_input_section = True
                in_output_section = False
                continue
            elif '🔊 Output Devices (Speakers/Headphones):' in line:
                in_input_section = False
                in_output_section = True
                continue
            elif '💡 To use specific devices' in line:
                break
            
            if in_input_section and line.strip().startswith('['):
                # Parse: [6] EarPods: USB Audio (hw:3,0) (channels: 1)
                parts = line.strip().split('] ', 1)
                if len(parts) == 2:
                    device_id = parts[0][1:]  # Remove the [
                    device_info = parts[1]
                    # Extract name and channels
                    if ' (channels:' in device_info:
                        name_part, channels_part = device_info.rsplit(' (channels:', 1)
                        channels = int(channels_part.split(')')[0])
                    else:
                        name_part = device_info
                        channels = 1
                    
                    input_devices.append({
                        'id': device_id,
                        'name': name_part.strip(),
                        'channels': channels
                    })
            
            elif in_output_section and line.strip().startswith('['):
                # Parse: [6] EarPods: USB Audio (hw:3,0) (channels: 2)
                parts = line.strip().split('] ', 1)
                if len(parts) == 2:
                    device_id = parts[0][1:]  # Remove the [
                    device_info = parts[1]
                    # Extract name and channels
                    if ' (channels:' in device_info:
                        name_part, channels_part = device_info.rsplit(' (channels:', 1)
                        channels = int(channels_part.split(')')[0])
                    else:
                        name_part = device_info
                        channels = 1
                    
                    output_devices.append({
                        'id': device_id,
                        'name': name_part.strip(),
                        'channels': channels
                    })
        
        return {
            'inputs': input_devices,
            'outputs': output_devices
        }
        
    except subprocess.CalledProcessError as e:
        print(f"Error running device_list: {e}", file=sys.stderr)
        return {'inputs': [], 'outputs': []}
    except FileNotFoundError:
        print("Error: device_list executable not found. Make sure to compile it first.", file=sys.stderr)
        return {'inputs': [], 'outputs': []}

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        devices = get_audio_devices()
        print(json.dumps(devices, indent=2))
    else:
        devices = get_audio_devices()
        print("🎤 Audio Devices:")
        print("\nInput Devices (Microphones):")
        for device in devices['inputs']:
            print(f"   [{device['id']}] {device['name']} (channels: {device['channels']})")
        
        print("\n🔊 Output Devices (Speakers/Headphones):")
        for device in devices['outputs']:
            print(f"   [{device['id']}] {device['name']} (channels: {device['channels']})")
        
        print("\n💡 Use --json flag for machine-readable output")

if __name__ == "__main__":
    main()
