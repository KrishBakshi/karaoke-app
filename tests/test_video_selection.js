#!/usr/bin/env node

// Test script to verify video selection logic
const fs = require('fs');
const path = require('path');

function testVideoSelection() {
  const songsDir = path.join(__dirname, 'autotune-app', 'songs');
  
  if (!fs.existsSync(songsDir)) {
    console.log('❌ Songs directory not found:', songsDir);
    return;
  }

  try {
    const songDirs = fs.readdirSync(songsDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);

    console.log('🎵 Testing video selection for songs:');
    console.log('=====================================');

    songDirs.forEach(dirName => {
      const songPath = path.join(songsDir, dirName);
      const videoFiles = fs.readdirSync(songPath)
        .filter(file => file.endsWith('.mp4') || file.endsWith('.webm'))
        .map(file => path.join('autotune-app', 'songs', dirName, file));

      // Test the selection logic
      const primaryVideo = videoFiles.find(f => f.includes('_karaoke.mp4')) || 
                          videoFiles.find(f => f.includes('karaoke')) || 
                          videoFiles[0];

      console.log(`\n🎤 ${dirName}:`);
      console.log(`   📁 All videos: ${videoFiles.length} files`);
      videoFiles.forEach(video => {
        const size = fs.statSync(path.join(__dirname, video)).size;
        const sizeMB = (size / (1024 * 1024)).toFixed(1);
        const isPrimary = video === primaryVideo;
        console.log(`      ${isPrimary ? '⭐' : '  '} ${video} (${sizeMB}MB)${isPrimary ? ' ← SELECTED' : ''}`);
      });
    });

  } catch (error) {
    console.error('❌ Error testing video selection:', error);
  }
}

testVideoSelection();
