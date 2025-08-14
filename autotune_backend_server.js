const WebSocket = require('ws');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const wss = new WebSocket.Server({ port: 8765 });

console.log('🎤 Autotune Karaoke Backend Server');
console.log('🚀 Listening on ws://localhost:8765');
console.log('🎵 Backend: autotune-app/');

// Global state
let currentSession = null;
let availableSongs = [];

// Discover available songs on startup
function discoverSongs() {
  const songsDir = path.join(__dirname, 'autotune-app', 'songs');
  if (!fs.existsSync(songsDir)) {
    console.log('⚠️  Songs directory not found:', songsDir);
    return;
  }

  try {
    const songDirs = fs.readdirSync(songsDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);

    availableSongs = songDirs.map(dirName => {
      // Extract clean song name
      const cleanName = dirName
        .replace(/_[a-f0-9]+_\d{8}_\d{6}$/, '') // Remove timestamp
        .replace(/_Official_Video$/, '') // Remove official video suffix
        .replace(/_/g, ' '); // Replace underscores with spaces

      // Check for video files
      const songPath = path.join(songsDir, dirName);
      const videoFiles = fs.readdirSync(songPath)
        .filter(file => file.endsWith('.mp4') || file.endsWith('.webm'))
        .map(file => path.join('autotune-app', 'songs', dirName, file));

      return {
        id: dirName,
        title: cleanName,
        directory: dirName,
        hasMelody: fs.existsSync(path.join(songsDir, dirName, `${dirName}_melody.txt`)) || 
                   fs.existsSync(path.join(songsDir, dirName, `${dirName.replace(/_.*$/, '')}_melody.txt`)) ||
                   fs.existsSync(path.join(songsDir, dirName, `${dirName.replace(/_[a-f0-9]+_\d{8}_\d{6}$/, '')}_melody.txt`)) ||
                   fs.existsSync(path.join(songsDir, dirName, `${dirName.replace(/_[a-f0-9]+_\d{8}_\d{6}$/, '').replace(/_.*$/, '')}_melody.txt`)) ||
                   fs.readdirSync(path.join(songsDir, dirName)).some(file => file.includes('melody.txt')),
        hasInstrumental: fs.existsSync(path.join(songsDir, dirName, `${dirName}_separated`)) ||
                         fs.existsSync(path.join(songsDir, dirName, `${dirName.replace(/_.*$/, '')}_separated`)) ||
                         fs.existsSync(path.join(songsDir, dirName, `${dirName.replace(/_[a-f0-9]+_\d{8}_\d{6}$/, '')}_separated`)) ||
                         fs.existsSync(path.join(songsDir, dirName, `${dirName.replace(/_[a-f0-9]+_\d{8}_\d{6}$/, '').replace(/_.*$/, '')}_separated`)) ||
                         fs.readdirSync(path.join(songsDir, dirName)).some(file => file.includes('separated')),
        videoFiles: videoFiles,
        primaryVideo: videoFiles.find(f => f.includes('_karaoke.mp4')) || videoFiles.find(f => f.includes('karaoke')) || videoFiles[0]
      };
    });

    console.log(`✅ Discovered ${availableSongs.length} songs:`, availableSongs.map(s => s.title));
  } catch (error) {
    console.error('❌ Error discovering songs:', error);
  }
}

// Run autotune karaoke with Python wrapper
function runKaraoke(songName, ws) {
  // Check if there's already a running process
  if (currentSession && currentSession.process) {
    ws.send(JSON.stringify({ 
      type: 'error', 
      message: 'Session already in progress. Stop current session first.' 
    }));
    return;
  }

  console.log(`🎵 Starting karaoke session for: ${songName}`);
  
  const pythonScript = path.join(__dirname, 'autotune-app', 'run_karaoke.py');
  const songDir = path.join(__dirname, 'autotune-app', 'songs', songName);
  
  if (!fs.existsSync(songDir)) {
    ws.send(JSON.stringify({ 
      type: 'error', 
      message: `Song directory not found: ${songName}` 
    }));
    return;
  }

  // Create or update session
  if (!currentSession) {
    currentSession = {
      songName,
      startTime: Date.now(),
      process: null,
      ws
    };
  } else {
    // Update existing session
    currentSession.songName = songName;
    currentSession.ws = ws;
  }

  // Start the Python wrapper with voice effect parameters
  const voiceEffects = currentSession.voiceEffects || {
    autotune: 1.0,
    pitch_shift: 0,
    voice_volume: 1.1,
    instrument_volume: 2.0,
    enable_chorus: false,
    chorus_depth: 0.1,
    enable_reverb: false,
    reverb_wetness: 0.3
  };
  
  console.log(`🎛️ Using voice effects:`, voiceEffects);
  
  const pythonArgs = [
    pythonScript, 
    songName,
    '--autotune', voiceEffects.autotune.toString(),
    '--pitch-shift', voiceEffects.pitch_shift.toString(),
    '--voice-volume', voiceEffects.voice_volume.toString(),
    '--instrument-volume', voiceEffects.instrument_volume.toString(),
    '--enable-chorus', voiceEffects.enable_chorus ? '1' : '0',
    '--chorus-depth', voiceEffects.chorus_depth.toString(),
    '--enable-reverb', voiceEffects.enable_reverb ? '1' : '0',
    '--reverb-wetness', voiceEffects.reverb_wetness.toString()
  ];
  
  console.log('🐍 Starting Python with args:', pythonArgs);
  
  // Create initial parameter file for real-time updates
  const paramFilePath = path.join(__dirname, 'autotune-app', 'voice_params.txt');
  try {
    const initialParams = [
      `voice_volume=${voiceEffects.voice_volume}`,
      `instrument_volume=${voiceEffects.instrument_volume}`,
      `autotune_strength=${voiceEffects.autotune}`,
      `pitch_shift=${voiceEffects.pitch_shift}`
    ].join('\n') + '\n';
    
    fs.writeFileSync(paramFilePath, initialParams);
    console.log(`📝 Initial parameters written to file:`, {
      voice_volume: voiceEffects.voice_volume,
      instrument_volume: voiceEffects.instrument_volume,
      autotune_strength: voiceEffects.autotune,
      pitch_shift: voiceEffects.pitch_shift
    });
  } catch (error) {
    console.error('❌ Failed to write initial parameters to file:', error);
  }
  
  const pythonProcess = spawn('python3', pythonArgs, {
    cwd: path.join(__dirname, 'autotune-app'),
    stdio: ['pipe', 'pipe', 'pipe']
  });

  currentSession.process = pythonProcess;

  // Handle Python output
  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString().trim();
    console.log('🐍 Python output:', output);
    
    if (output.includes('Starting karaoke')) {
      console.log('🎤 C++ Karaoke backend started successfully!');
      ws.send(JSON.stringify({ 
        type: 'state', 
        playing: true, 
        positionSec: 0,
        song: { id: songName, title: songName.replace(/_/g, ' '), durationSec: 180 }
      }));
    }
    
    if (output.includes('C++ Karaoke with Recording started')) {
      console.log('🎵 C++ backend is now recording and processing audio!');
      ws.send(JSON.stringify({ 
        type: 'backend_status', 
        status: 'recording',
        message: 'C++ backend is now recording and processing audio'
      }));
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    const error = data.toString().trim();
    console.error('🐍 Python error:', error);
    
    if (error.includes('not found') || error.includes('failed')) {
      ws.send(JSON.stringify({ 
        type: 'error', 
        message: `Karaoke failed to start: ${error}` 
      }));
      stopSession();
    }
  });

  pythonProcess.on('close', (code) => {
    console.log(`🎵 Karaoke session ended with code: ${code}`);
    if (currentSession && currentSession.songName === songName) {
      ws.send(JSON.stringify({ 
        type: 'state', 
        playing: false, 
        positionSec: 0 
      }));
      stopSession();
    }
  });

  pythonProcess.on('error', (error) => {
    console.error('❌ Failed to start karaoke:', error);
    ws.send(JSON.stringify({ 
      type: 'error', 
      message: `Failed to start karaoke: ${error.message}` 
    }));
    stopSession();
  });
}

// Stop current session (preserves session data for restarting)
function stopSession() {
  if (currentSession && currentSession.process) {
    console.log('🛑 Stopping karaoke session...');
    currentSession.process.kill('SIGTERM');
    
    // Force kill after 5 seconds if still running
    setTimeout(() => {
      if (currentSession && currentSession.process) {
        currentSession.process.kill('SIGKILL');
      }
    }, 5000);
  }
  
  // Don't clear the entire session, just the process
  // This preserves song name and voice effects for restarting
  if (currentSession) {
    currentSession.process = null;
  }
}

// Clear session completely (used when loading new songs)
function clearSession() {
  if (currentSession && currentSession.process) {
    stopSession();
  }
  currentSession = null;
}

// WebSocket connection handler
wss.on('connection', (ws) => {
  console.log('🎧 Client connected');
  
  // Send available songs immediately
  ws.send(JSON.stringify({ 
    type: 'songs_list', 
    songs: availableSongs 
  }));

  ws.on('message', (raw) => {
    console.log('📥 Raw message received:', raw);
    console.log('📥 Raw message type:', typeof raw);
    console.log('📥 Raw message constructor:', raw.constructor.name);
    console.log('📥 Raw message toString():', raw.toString());
    console.log('📥 Raw message buffer length:', raw.length || 'N/A');
    
    let msg = {};
    try { 
      const rawString = raw.toString();
      console.log('📥 Raw string length:', rawString.length);
      console.log('📥 Raw string first 100 chars:', rawString.substring(0, 100));
      console.log('📥 Raw string last 100 chars:', rawString.substring(Math.max(0, rawString.length - 100)));
      
      // Check for hidden characters or encoding issues
      console.log('📥 Raw string char codes (first 20):', Array.from(rawString.substring(0, 20)).map(c => c.charCodeAt(0)));
      
      msg = JSON.parse(rawString); 
    } catch (error) {
      console.error('❌ Invalid JSON message:', error);
      console.error('❌ Raw message was:', raw);
      console.error('❌ Raw string was:', rawString);
      return;
    }

    // Check if message might be double-encoded
    if (typeof msg === 'string') {
      console.log('⚠️  Message is a string, attempting to parse again...');
      try {
        msg = JSON.parse(msg);
      } catch (error) {
        console.error('❌ Failed to parse double-encoded message:', error);
        return;
      }
    }
    
    // Handle double-encoded messages where action contains JSON string
    if (msg.action && typeof msg.action === 'string' && msg.action.startsWith('{')) {
      console.log('⚠️  Detected double-encoded message, parsing action field...');
      try {
        const decodedAction = JSON.parse(msg.action);
        msg = decodedAction;
        console.log('✅ Successfully decoded double-encoded message:', msg);
      } catch (error) {
        console.error('❌ Failed to parse double-encoded action field:', error);
        console.error('❌ Raw action field was:', msg.action);
        return;
      }
    }
    
    // Additional check: if the entire message looks like it might be double-encoded
    if (Object.keys(msg).length === 1 && msg.action && typeof msg.action === 'string' && msg.action.includes('"action"')) {
      console.log('⚠️  Detected potential double-encoded message structure, attempting to parse...');
      console.log('📥 Message keys count:', Object.keys(msg).length);
      console.log('📥 Action field content:', msg.action);
      try {
        const decodedMessage = JSON.parse(msg.action);
        console.log('📥 Decoded message:', decodedMessage);
        if (decodedMessage.action && decodedMessage.payload) {
          msg = decodedMessage;
          console.log('✅ Successfully decoded double-encoded message structure:', msg);
        } else {
          console.log('⚠️  Decoded message missing action or payload fields');
        }
      } catch (error) {
        console.error('❌ Failed to parse potential double-encoded message:', error);
      }
    }
    
    // Final fallback: if we still have a string action that looks like JSON, try to parse it
    if (msg.action && typeof msg.action === 'string' && msg.action.trim().startsWith('{') && msg.action.trim().endsWith('}')) {
      console.log('🔄 Final fallback: attempting to parse action as JSON...');
      try {
        const fallbackDecoded = JSON.parse(msg.action.trim());
        if (fallbackDecoded.action && fallbackDecoded.payload) {
          console.log('✅ Fallback parsing successful:', fallbackDecoded);
          msg = fallbackDecoded;
        }
      } catch (error) {
        console.error('❌ Fallback parsing failed:', error);
      }
    }
    
    // Ensure msg is an object
    if (typeof msg !== 'object' || msg === null) {
      console.error('❌ Message is not an object:', typeof msg, msg);
      return;
    }
    
    // Try destructuring first, fallback to direct access
    let action, payload;
    try {
      ({ action, payload } = msg);
    } catch (error) {
      console.error('❌ Destructuring failed, trying direct access:', error);
      action = msg.action;
      payload = msg.payload;
    }
    
    console.log('📨 Parsed message object:', msg);
    console.log('📨 Message keys:', Object.keys(msg));
    console.log('📨 Parsed action:', action, 'payload:', payload);

    if (!action) {
      console.error('❌ Message missing action field:', msg);
      console.error('❌ Available keys:', Object.keys(msg));
      return;
    }

    switch (action) {
      case 'load_song':
        const songId = payload?.songId;
        const inputDevice = payload?.inputDevice;
        const outputDevice = payload?.outputDevice;
        
        if (songId) {
          const song = availableSongs.find(s => s.id === songId);
          if (song) {
            // Store device settings in session
            if (!currentSession) {
              currentSession = {
                songName: song.directory,
                startTime: Date.now(),
                process: null,
                ws,
                inputDevice: inputDevice || 'default',
                outputDevice: outputDevice || 'default'
              };
            } else {
              currentSession.songName = song.directory;
              currentSession.inputDevice = inputDevice || 'default';
              currentSession.outputDevice = outputDevice || 'default';
            }
            
            console.log(`🎵 Song loaded: ${song.title}`);
            console.log(`🎤 Input device: ${currentSession.inputDevice}`);
            console.log(`🔊 Output device: ${currentSession.outputDevice}`);
            
            ws.send(JSON.stringify({ 
              type: 'song_loaded', 
              song: song,
              inputDevice: currentSession.inputDevice,
              outputDevice: currentSession.outputDevice
            }));
            
            // Automatically start the karaoke session after loading the song
            console.log(`🚀 Auto-starting karaoke session for: ${song.title}`);
            setTimeout(() => {
              runKaraoke(currentSession.songName, ws);
            }, 500); // Small delay to ensure song_loaded message is sent first
          } else {
            ws.send(JSON.stringify({ 
              type: 'error', 
              message: `Song not found: ${songId}` 
            }));
          }
        }
        break;

      case 'start_session':
        if (currentSession && currentSession.songName) {
          console.log(`🚀 Starting session with song: ${currentSession.songName}`);
          console.log(`🎤 Using input device: ${currentSession.inputDevice || 'default'}`);
          console.log(`🔊 Using output device: ${currentSession.outputDevice || 'default'}`);
          runKaraoke(currentSession.songName, ws);
        } else {
          ws.send(JSON.stringify({ 
            type: 'error', 
            message: 'No song loaded. Please select a song first.' 
          }));
        }
        break;

      case 'stop_session':
        clearSession();
        ws.send(JSON.stringify({ 
          type: 'state', 
          playing: false, 
          positionSec: 0 
        }));
        break;

      case 'pause':
        // Note: C++ backend doesn't support pause/resume, so we'll simulate it
        if (currentSession) {
          ws.send(JSON.stringify({ 
            type: 'state', 
            playing: false, 
            positionSec: (Date.now() - currentSession.startTime) / 1000 
          }));
        }
        break;

      case 'resume':
        if (currentSession) {
          ws.send(JSON.stringify({ 
            type: 'state', 
            playing: true, 
            positionSec: (Date.now() - currentSession.startTime) / 1000 
          }));
        }
        break;

      case 'refresh_songs':
        discoverSongs();
        ws.send(JSON.stringify({ 
          type: 'songs_list', 
          songs: availableSongs 
        }));
        break;

      case 'set_voice_effect':
        if (currentSession && currentSession.process) {
          const { effect, value } = payload;
          
          // Store the voice effect setting in the session
          if (!currentSession.voiceEffects) {
            currentSession.voiceEffects = {
              autotune: 1.0,
              pitch_shift: 0,
              voice_volume: 1.1,
              instrument_volume: 2.0,
              enable_chorus: false,
              chorus_depth: 0.1,
              enable_reverb: false,
              reverb_wetness: 0.3
            };
          }
          
          // Update the specific effect
          if (effect === 'autotune') {
            currentSession.voiceEffects.autotune = value;
          } else if (effect === 'pitch_shift') {
            currentSession.voiceEffects.pitch_shift = value;
          } else if (effect === 'voice_volume') {
            currentSession.voiceEffects.voice_volume = value;
          } else if (effect === 'enable_chorus') {
            currentSession.voiceEffects.enable_chorus = value;
          } else if (effect === 'chorus_depth') {
            currentSession.voiceEffects.chorus_depth = value;
          } else if (effect === 'enable_reverb') {
            currentSession.voiceEffects.enable_reverb = value;
          } else if (effect === 'reverb_wetness') {
            currentSession.voiceEffects.reverb_wetness = value;
          }
          
          ws.send(JSON.stringify({ 
            type: 'voice_effect_updated', 
            effect, 
            value 
          }));
          
          console.log(`🎛️ Voice effect updated: ${effect} = ${value}`);
          
          // Only restart session for effects that require restart (chorus and reverb)
          const effectsRequiringRestart = ['enable_chorus', 'chorus_depth', 'enable_reverb', 'reverb_wetness'];
          
          if (effectsRequiringRestart.includes(effect)) {
            console.log('🔄 Restarting karaoke session with updated voice effects...');
            stopSession();
            setTimeout(() => {
              runKaraoke(currentSession.songName, ws);
            }, 1000); // Small delay to ensure clean shutdown
          } else if (['voice_volume', 'instrument_volume', 'autotune', 'pitch_shift'].includes(effect)) {
            // Update real-time parameters by writing to parameter file
            console.log(`✅ ${effect} updated - writing to parameter file for real-time update`);
            const paramFilePath = path.join(__dirname, 'autotune-app', 'voice_params.txt');
            try {
              // Read existing parameters
              let existingParams = {};
              if (fs.existsSync(paramFilePath)) {
                const content = fs.readFileSync(paramFilePath, 'utf8');
                content.split('\n').forEach(line => {
                  if (line.trim()) {
                    const [key, value] = line.split('=');
                    if (key && value) {
                      existingParams[key.trim()] = value.trim();
                    }
                  }
                });
              }
              
              // Update the specific parameter
              if (effect === 'voice_volume') {
                existingParams['voice_volume'] = value;
              } else if (effect === 'instrument_volume') {
                existingParams['instrument_volume'] = value;
              } else if (effect === 'autotune') {
                existingParams['autotune_strength'] = value;
              } else if (effect === 'pitch_shift') {
                existingParams['pitch_shift'] = value;
              }
              
              // Write all parameters back to file
              const paramContent = Object.entries(existingParams)
                .map(([key, val]) => `${key}=${val}`)
                .join('\n') + '\n';
              
              fs.writeFileSync(paramFilePath, paramContent);
              console.log(`📝 ${effect} parameter updated in file: ${value}`);
            } catch (error) {
              console.error(`❌ Failed to update ${effect} parameter in file:`, error);
            }
          } else {
            console.log('✅ Effect updated - no session restart needed');
          }
        }
        break;

      case 'set_voice_effects':
        if (currentSession && currentSession.process) {
          const effects = payload;
          
          // Store the voice effects in the session
          if (!currentSession.voiceEffects) {
            currentSession.voiceEffects = {
              autotune: 1.0,
              pitch_shift: 0,
              voice_volume: 1.1,
              instrument_volume: 2.0,
              enable_chorus: false,
              chorus_depth: 0.1,
              enable_reverb: false,
              reverb_wetness: 0.3
            };
          }
          
          // Check if only real-time updatable effects are being updated
          const effectsRequiringRestart = ['enable_chorus', 'chorus_depth', 'enable_reverb', 'reverb_wetness'];
          const hasEffectsRequiringRestart = effectsRequiringRestart.some(effect => effects.hasOwnProperty(effect));
          
          // Update all effects
          Object.assign(currentSession.voiceEffects, effects);
          
          ws.send(JSON.stringify({ 
            type: 'voice_effects_updated', 
            effects: currentSession.voiceEffects
          }));
          
          console.log(`🎛️ Voice effects updated:`, currentSession.voiceEffects);
          
          // Only restart if effects requiring restart are being updated
          if (hasEffectsRequiringRestart) {
            console.log('🔄 Restarting karaoke session with updated voice effects...');
            stopSession();
            setTimeout(() => {
              runKaraoke(currentSession.songName, ws);
            }, 1000); // Small delay to ensure clean shutdown
          } else {
            // Check for real-time updatable effects and write to parameter file
            const realTimeEffects = ['voice_volume', 'instrument_volume', 'autotune', 'pitch_shift'];
            let hasRealTimeUpdates = false;
            
            // Read existing parameters first
            let existingParams = {};
            const paramFilePath = path.join(__dirname, 'autotune-app', 'voice_params.txt');
            if (fs.existsSync(paramFilePath)) {
              try {
                const content = fs.readFileSync(paramFilePath, 'utf8');
                content.split('\n').forEach(line => {
                  if (line.trim()) {
                    const [key, value] = line.split('=');
                    if (key && value) {
                      existingParams[key.trim()] = value.trim();
                    }
                  }
                });
              } catch (error) {
                console.error('❌ Failed to read existing parameters:', error);
              }
            }
            
            for (const effect of realTimeEffects) {
              if (effects.hasOwnProperty(effect)) {
                hasRealTimeUpdates = true;
                console.log(`✅ ${effect} updated - updating parameter file for real-time update`);
                try {
                  // Update the specific parameter
                  if (effect === 'voice_volume') {
                    existingParams['voice_volume'] = effects[effect];
                  } else if (effect === 'instrument_volume') {
                    existingParams['instrument_volume'] = effects[effect];
                  } else if (effect === 'autotune') {
                    existingParams['autotune_strength'] = effects[effect];
                  } else if (effect === 'pitch_shift') {
                    existingParams['pitch_shift'] = effects[effect];
                  }
                } catch (error) {
                  console.error(`❌ Failed to update ${effect} parameter:`, error);
                }
              }
            }
            
            // Write all updated parameters back to file
            if (hasRealTimeUpdates) {
              try {
                const paramContent = Object.entries(existingParams)
                  .map(([key, val]) => `${key}=${val}`)
                  .join('\n') + '\n';
                
                fs.writeFileSync(paramFilePath, paramContent);
                console.log(`📝 All real-time parameters updated in file`);
              } catch (error) {
                console.error('❌ Failed to write updated parameters to file:', error);
              }
            }
            
            if (hasRealTimeUpdates) {
              console.log('✅ Real-time effects updated - no session restart needed');
            } else {
              console.log('✅ No effects requiring restart or real-time updates');
            }
          }
        }
        break;

      case 'set_voice_preset':
        if (currentSession && currentSession.process) {
          const { preset } = payload;
          
          // Define voice presets
          const presets = {
            'Natural': { autotune: 0.3, pitch_shift: 0, voice_volume: 1.0, instrument_volume: 2.0 },
            'Autotune': { autotune: 1.0, pitch_shift: 0, voice_volume: 1.1, instrument_volume: 2.0 },
            'Chipmunk': { autotune: 0.8, pitch_shift: 7, voice_volume: 1.2, instrument_volume: 2.0 },
            'Deep Voice': { autotune: 0.6, pitch_shift: -7, voice_volume: 1.3, instrument_volume: 2.0 },
            'Robot': { autotune: 1.0, pitch_shift: 0, voice_volume: 1.0, instrument_volume: 2.0, enable_chorus: true },
            'Angelic': { autotune: 0.9, pitch_shift: 2, voice_volume: 1.4, instrument_volume: 2.0, enable_reverb: true }
          };
          
          if (presets[preset]) {
            const preset_data = presets[preset];
            
            // Store the preset in the session
            if (!currentSession.voiceEffects) {
              currentSession.voiceEffects = {};
            }
            Object.assign(currentSession.voiceEffects, preset_data);
            
            ws.send(JSON.stringify({ 
              type: 'voice_preset_applied', 
              preset, 
              settings: preset_data 
            }));
            
            console.log(`🎭 Voice preset applied: ${preset}`, preset_data);
            
            // Restart the session with new voice effects
            console.log('🔄 Restarting karaoke session with updated voice preset...');
            stopSession();
            setTimeout(() => {
              runKaraoke(currentSession.songName, ws);
            }, 1000); // Small delay to ensure clean shutdown
          }
        }
        break;
    
      default:
        console.log('⚠️  Unknown action:', action);
    }
  });

  ws.on('close', () => {
    console.log('🎧 Client disconnected');
    // Stop session if this client was controlling it
    if (currentSession && currentSession.ws === ws) {
      stopSession();
    }
  });

  ws.on('error', (error) => {
    console.error('❌ WebSocket error:', error);
  });
});

// Discover songs on startup
discoverSongs();

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down...');
  if (currentSession) {
    stopSession();
  }
  wss.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Received SIGTERM, shutting down...');
  if (currentSession) {
    stopSession();
  }
  wss.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});
