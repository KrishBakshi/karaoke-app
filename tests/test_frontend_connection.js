#!/usr/bin/env node

// Test script to simulate frontend connection
const WebSocket = require('ws');

console.log('🔍 Testing frontend connection simulation...');

const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
  console.log('✅ Connected to backend (simulating frontend)');
  
  // Simulate what the frontend does on connection
  console.log('📨 Requesting songs list (like frontend does)...');
  ws.send(JSON.stringify({ action: 'refresh_songs' }));
  
  // Also test loading a song
  setTimeout(() => {
    console.log('📨 Testing song selection...');
    ws.send(JSON.stringify({ action: 'load_song', payload: { songId: 'Taylor_Swift_-_Love_Story_f66263_20250811_202548' } }));
  }, 1000);
});

ws.on('message', (data) => {
  try {
    const message = JSON.parse(data.toString());
    console.log('📨 Received message:', JSON.stringify(message, null, 2));
    
    if (message.type === 'songs_list') {
      console.log('\n🎵 Songs received by frontend:');
      message.songs.forEach(song => {
        console.log(`  🎤 ${song.title}`);
        console.log(`     Primary Video: ${song.primaryVideo || 'NONE'}`);
        console.log(`     Video Files: ${song.videoFiles ? song.videoFiles.length : 0} files`);
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

// Close after 10 seconds
setTimeout(() => {
  ws.close();
  process.exit(0);
}, 10000);
