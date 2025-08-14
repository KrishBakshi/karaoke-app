#!/usr/bin/env python3
"""
Integration Test Script for Autotune Karaoke System
This script tests the integration between all components.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

def test_song_discovery():
    """Test song discovery functionality."""
    print("🔍 Testing song discovery...")
    
    try:
        # Test the integration bridge
        result = subprocess.run(
            ["python3", "integration_bridge.py", "discover"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            songs_data = json.loads(result.stdout)
            songs = songs_data.get("songs", [])
            
            print(f"✅ Found {len(songs)} songs:")
            for song in songs:
                print(f"   🎵 {song['title']}")
                print(f"      Melody: {'✅' if song['hasMelody'] else '❌'}")
                print(f"      Instrumental: {'✅' if song['hasInstrumental'] else '❌'}")
            
            return len(songs) > 0
        else:
            print(f"❌ Song discovery failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Song discovery error: {e}")
        return False

def test_backend_connection():
    """Test backend WebSocket connection."""
    print("\n🔌 Testing backend connection...")
    
    try:
        # Check if backend is running
        result = subprocess.run(
            ["lsof", "-ti:8765"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Backend server is running on port 8765")
            return True
        else:
            print("❌ Backend server is not running on port 8765")
            return False
            
    except Exception as e:
        print(f"❌ Backend connection test error: {e}")
        return False

def test_frontend_connection():
    """Test frontend HTTP server."""
    print("\n🌐 Testing frontend connection...")
    
    try:
        # Check if frontend is running
        result = subprocess.run(
            ["lsof", "-ti:3000"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Frontend server is running on port 3000")
            return True
        else:
            print("❌ Frontend server is not running on port 3000")
            return False
            
    except Exception as e:
        print(f"❌ Frontend connection test error: {e}")
        return False

def test_autotune_executable():
    """Test if autotune executable exists and is runnable."""
    print("\n🎤 Testing autotune executable...")
    
    autotune_path = Path("autotune-app/autotune-karaoke")
    
    if not autotune_path.exists():
        print("❌ autotune-karaoke executable not found")
        return False
    
    if not os.access(autotune_path, os.X_OK):
        print("❌ autotune-karaoke is not executable")
        return False
    
    print("✅ autotune-karaoke executable found and runnable")
    return True

def test_python_dependencies():
    """Test Python dependencies."""
    print("\n🐍 Testing Python dependencies...")
    
    try:
        import numpy
        print("✅ numpy is available")
    except ImportError:
        print("❌ numpy is not available")
        return False
    
    try:
        from pathlib import Path
        print("✅ pathlib is available")
    except ImportError:
        print("❌ pathlib is not available")
        return False
    
    return True

def test_node_dependencies():
    """Test Node.js dependencies."""
    print("\n📦 Testing Node.js dependencies...")
    
    if not Path("node_modules").exists():
        print("❌ node_modules not found")
        return False
    
    if not Path("node_modules/ws").exists():
        print("❌ ws package not found")
        return False
    
    print("✅ Node.js dependencies are installed")
    return True

def main():
    """Run all integration tests."""
    print("🎤 Autotune Karaoke System - Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Python Dependencies", test_python_dependencies),
        ("Node.js Dependencies", test_node_dependencies),
        ("Autotune Executable", test_autotune_executable),
        ("Song Discovery", test_song_discovery),
        ("Backend Connection", test_backend_connection),
        ("Frontend Connection", test_frontend_connection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\n💡 To start the system, run:")
        print("   ./start_autotune_system.sh")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print("\n💡 Common solutions:")
        print("   1. Run: ./start_autotune_system.sh")
        print("   2. Check if ports 3000 and 8765 are available")
        print("   3. Ensure autotune-app is built")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
