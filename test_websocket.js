const WebSocket = require('ws');

// Test the WebSocket server
const ws = new WebSocket('ws://localhost:8765');

ws.on('open', () => {
  console.log('🔌 Connected to WebSocket server');
  
  // Test 1: Load a song (this was the double-encoded message)
  const loadSongMessage = {
    action: 'load_song',
    payload: {
      songId: 'Again_6fbf74_20250813_183754',
      inputDevice: '5',
      outputDevice: '0'
    }
  };
  
  console.log('📤 Sending load_song message:', JSON.stringify(loadSongMessage));
  ws.send(JSON.stringify(loadSongMessage));
  
  // Test 2: Set voice effect
  setTimeout(() => {
    const voiceEffectMessage = {
      action: 'set_voice_effect',
      payload: {
        effect: 'autotune',
        value: 0.8
      }
    };
    
    console.log('📤 Sending set_voice_effect message:', JSON.stringify(voiceEffectMessage));
    ws.send(JSON.stringify(voiceEffectMessage));
  }, 1000);
  
  // Test 3: Set voice preset
  setTimeout(() => {
    const voicePresetMessage = {
      action: 'set_voice_preset',
      payload: {
        preset: 'Robot'
      }
    };
    
    console.log('📤 Sending set_voice_preset message:', JSON.stringify(voicePresetMessage));
    ws.send(JSON.stringify(voicePresetMessage));
  }, 2000);
  
  // Close after tests
  setTimeout(() => {
    console.log('🔌 Closing connection');
    ws.close();
    process.exit(0);
  }, 3000);
});

ws.on('message', (data) => {
  try {
    const message = JSON.parse(data.toString());
    console.log('📥 Received message:', message);
  } catch (error) {
    console.log('📥 Received raw message:', data.toString());
  }
});

ws.on('error', (error) => {
  console.error('❌ WebSocket error:', error);
});

ws.on('close', () => {
  console.log('🔌 Connection closed');
});
