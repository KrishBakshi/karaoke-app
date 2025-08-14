#!/usr/bin/env node

// Debug script to test WebSocket communication
const WebSocket = require('ws');

console.log('🔍 Testing WebSocket connection to backend...');

const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
  console.log('✅ Connected to backend');
  
  // Request songs list
  console.log('📨 Requesting songs list...');
  ws.send(JSON.stringify({ action: 'refresh_songs' }));
});

ws.on('message', (data) => {
  try {
    const message = JSON.parse(data.toString());
    console.log('📨 Received message:', JSON.stringify(message, null, 2));
    
    if (message.type === 'songs_list') {
      console.log('\n🎵 Songs discovered:');
      message.songs.forEach(song => {
        console.log(`  🎤 ${song.title}`);
        console.log(`     ID: ${song.id}`);
        console.log(`     Melody: ${song.hasMelody ? '✅' : '❌'}`);
        console.log(`     Instrumental: ${song.hasInstrumental ? '✅' : '❌'}`);
        if (song.videoFiles) {
          console.log(`     Videos: ${song.videoFiles.length} files`);
          song.videoFiles.forEach(video => console.log(`       - ${video}`));
        }
        if (song.primaryVideo) {
          console.log(`     Primary: ${song.primaryVideo}`);
        }
        console.log('');
      });
    }
    
  } catch (error) {
    console.error('❌ Failed to parse message:', error);
  }
});

ws.on('error', (error) => {
  console.error('❌ WebSocket error:', error);
});

ws.on('close', () => {
  console.log('🔌 WebSocket closed');
});

// Close after 5 seconds
setTimeout(() => {
  ws.close();
  process.exit(0);
}, 5000);
