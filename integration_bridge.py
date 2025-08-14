#!/usr/bin/env python3
"""
Integration Bridge for Autotune Karaoke System
This script provides a clean API interface between the Node.js backend and C++ autotune system.
"""

import os
import sys
import json
import subprocess
import signal
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class AutotuneIntegrationBridge:
    def __init__(self, songs_dir: str = "autotune-app/songs"):
        self.songs_dir = Path(songs_dir)
        self.current_session = None
        self.process = None
        
    def discover_songs(self) -> List[Dict]:
        """Discover all available songs in the songs directory."""
        songs = []
        
        if not self.songs_dir.exists():
            return songs
            
        for song_dir in self.songs_dir.iterdir():
            if song_dir.is_dir():
                song_info = self._analyze_song_directory(song_dir)
                if song_info:
                    songs.append(song_info)
                    
        return songs
    
    def _analyze_song_directory(self, song_dir: Path) -> Optional[Dict]:
        """Analyze a song directory and extract metadata."""
        try:
            # Extract clean song name
            clean_name = self._extract_clean_song_name(song_dir.name)
            
            # Check for melody files
            melody_files = list(song_dir.glob("*melody.*"))
            has_melody = any(mf.suffix == ".txt" for mf in melody_files)
            
            # Check for instrumental files
            separated_dir = song_dir / f"{clean_name}_separated"
            if not separated_dir.exists():
                # Try alternative naming patterns
                for subdir in song_dir.iterdir():
                    if subdir.is_dir() and "separated" in subdir.name.lower():
                        separated_dir = subdir
                        break
            
            has_instrumental = separated_dir.exists() and any(
                "instrumental" in f.name.lower() 
                for f in separated_dir.iterdir() 
                if f.is_file()
            )
            
            return {
                "id": song_dir.name,
                "title": clean_name,
                "directory": song_dir.name,
                "hasMelody": has_melody,
                "hasInstrumental": has_instrumental,
                "melodyFiles": [str(mf) for mf in melody_files],
                "path": str(song_dir)
            }
        except Exception as e:
            print(f"⚠️  Error analyzing song directory {song_dir}: {e}")
            return None
    
    def _extract_clean_song_name(self, directory_name: str) -> str:
        """Extract a clean song name from directory name."""
        import re
        
        # Remove timestamp patterns like _f66263_20250811_202548
        timestamp_pattern = r'_[a-f0-9]+_\d{8}_\d{6}$'
        official_pattern = r'_Official_Video$'
        
        clean_name = re.sub(timestamp_pattern, '', directory_name)
        clean_name = re.sub(official_pattern, '', clean_name)
        
        return clean_name
    
    def start_karaoke_session(self, song_name: str) -> Dict:
        """Start a karaoke session with the specified song."""
        if self.current_session:
            return {
                "success": False,
                "error": "Session already in progress"
            }
        
        # Find song files
        melody_file, instrumental_file, message = self._find_song_files(song_name)
        
        if not melody_file or not instrumental_file:
            return {
                "success": False,
                "error": f"Song files not found: {message}"
            }
        
        try:
            # Start the C++ karaoke program
            cmd = ["./autotune-karaoke", song_name, melody_file, instrumental_file]
            
            print(f"🚀 Starting karaoke: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                cwd=Path("autotune-app"),  # Run from autotune-app directory
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.current_session = {
                "song_name": song_name,
                "start_time": time.time(),
                "melody_file": melody_file,
                "instrumental_file": instrumental_file,
                "process": self.process
            }
            
            return {
                "success": True,
                "message": f"Karaoke session started for {song_name}",
                "session": self.current_session
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start karaoke: {str(e)}"
            }
    
    def stop_karaoke_session(self) -> Dict:
        """Stop the current karaoke session."""
        if not self.current_session:
            return {
                "success": False,
                "error": "No active session"
            }
        
        try:
            if self.process:
                print("🛑 Stopping karaoke session...")
                
                # Send SIGTERM first
                self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("⚠️  Force killing process...")
                    self.process.kill()
                    self.process.wait()
                
                self.process = None
            
            session_info = self.current_session
            self.current_session = None
            
            return {
                "success": True,
                "message": "Karaoke session stopped",
                "session": session_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop session: {str(e)}"
            }
    
    def get_session_status(self) -> Dict:
        """Get the current session status."""
        if not self.current_session:
            return {
                "active": False,
                "message": "No active session"
            }
        
        if self.process:
            # Check if process is still running
            if self.process.poll() is None:
                return {
                    "active": True,
                    "song_name": self.current_session["song_name"],
                    "start_time": self.current_session["start_time"],
                    "duration": time.time() - self.current_session["start_time"],
                    "message": "Session active"
                }
            else:
                # Process has ended
                return_code = self.process.returncode
                self.current_session = None
                self.process = None
                
                return {
                    "active": False,
                    "return_code": return_code,
                    "message": f"Session ended with code {return_code}"
                }
        
        return {
            "active": False,
            "message": "Session inactive"
        }
    
    def _find_song_files(self, song_input: str) -> Tuple[Optional[str], Optional[str], str]:
        """Find song files using the existing song_finder logic."""
        try:
            # Import song_finder dynamically
            sys.path.insert(0, Path("autotune-app"))
            from song_finder import find_song_files
            
            return find_song_files(song_input)
            
        except ImportError:
            # Fallback if song_finder is not available
            return None, None, "song_finder module not available"
    
    def cleanup(self):
        """Cleanup resources."""
        if self.current_session:
            self.stop_karaoke_session()

def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("🎤 Autotune Integration Bridge")
        print("📖 Usage:")
        print("  python3 integration_bridge.py discover")
        print("  python3 integration_bridge.py start <song_name>")
        print("  python3 integration_bridge.py stop")
        print("  python3 integration_bridge.py status")
        return
    
    bridge = AutotuneIntegrationBridge()
    
    try:
        command = sys.argv[1]
        
        if command == "discover":
            songs = bridge.discover_songs()
            print(json.dumps({"songs": songs}, indent=2))
            
        elif command == "start":
            if len(sys.argv) < 3:
                print("❌ Song name required")
                return
            song_name = sys.argv[2]
            result = bridge.start_karaoke_session(song_name)
            print(json.dumps(result, indent=2))
            
        elif command == "stop":
            result = bridge.stop_karaoke_session()
            print(json.dumps(result, indent=2))
            
        elif command == "status":
            result = bridge.get_session_status()
            print(json.dumps(result, indent=2))
            
        else:
            print(f"❌ Unknown command: {command}")
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        bridge.cleanup()

if __name__ == "__main__":
    main()
