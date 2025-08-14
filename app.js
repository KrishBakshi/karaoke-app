import { initPitchRenderer } from './pitch_renderer_stub.js';

const e = React.createElement;

function usePitchRenderer() {
  const canvasRef = React.useRef(null);
  const disposerRef = React.useRef(null);
  const mount = React.useCallback(async () => {
    if (!canvasRef.current) return;
    disposerRef.current = await initPitchRenderer({
      canvas: canvasRef.current,
      onReady: () => {},
      onDispose: () => {},
    });
  }, []);
  const unmount = React.useCallback(() => {
    disposerRef.current && disposerRef.current();
  }, []);
  return { canvasRef, mount, unmount };
}

class WSClient {
  constructor(url){ 
    this.url=url; 
    this.listeners=new Set(); 
    this.connected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }
  
  connect(){ 
    this.ws=new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('🎧 WebSocket connected');
      this.connected = true;
      this.reconnectAttempts = 0;
    };
    
    this.ws.onclose = () => {
      console.log('🎧 WebSocket disconnected');
      this.connected = false;
      this.attemptReconnect();
    };
    
    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };
    
    this.ws.onmessage=(m)=>{ 
      try{
        const ev=JSON.parse(m.data); 
        this.listeners.forEach(l=>l(ev));
      }catch(error){
        console.error('❌ Failed to parse WebSocket message:', error);
      }
    };
  }
  
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => this.connect(), 2000 * this.reconnectAttempts);
    }
  }
  
  send(action,payload){ 
    if (this.connected && this.ws) {
      this.ws.send(JSON.stringify({action,payload})); 
    } else {
      console.warn('⚠️  WebSocket not connected, cannot send:', action);
    }
  }
  
  addListener(cb){ this.listeners.add(cb); }
  removeListener(cb){ this.listeners.delete(cb); }
}

function App(){
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const [sidebarWidth, setSidebarWidth] = React.useState(300);
  const [useMock, setUseMock] = React.useState(false);
  const [wsUrl, setWsUrl] = React.useState('ws://localhost:8765');
  const wsRef = React.useRef(null);
  const [playing, setPlaying] = React.useState(false);
  const [pos, setPos] = React.useState(0);
  const [song, setSong] = React.useState(null);
  const [songs, setSongs] = React.useState([]);
  const [error, setError] = React.useState(null);
  const [backendStatus, setBackendStatus] = React.useState('disconnected');
  const [videoSrc, setVideoSrc] = React.useState('');
  const videoRef = React.useRef(null);
  const [audioDevices, setAudioDevices] = React.useState({ inputs: [], outputs: [] });
  const [selectedInput, setSelectedInput] = React.useState('');
  const [selectedOutput, setSelectedOutput] = React.useState('');
  const [currentPreset, setCurrentPreset] = React.useState(null);

  // Remove the mock pitch renderer - we'll use C++ instead
  // const { canvasRef, mount, unmount } = usePitchRenderer();
  // React.useEffect(()=>{ mount(); return ()=>unmount(); },[mount,unmount]);

  React.useEffect(()=>{
    if (useMock) return;
    const ws = new WSClient(wsUrl); 
    wsRef.current = ws;
    
    const onEvent = (ev)=>{
      console.log('📨 Received event:', ev);
      
      switch(ev.type) {
        case 'state':
          setPlaying(ev.playing); 
          setPos(ev.positionSec || 0);
          break;
        case 'meta':
          setSong(ev.song); 
          break;
        case 'tick':
          setPos(ev.positionSec || 0); 
          break;
        case 'songs_list':
          setSongs(ev.songs || []);
          break;
        case 'voice_preset_applied':
          setCurrentPreset(ev.preset);
          console.log('✅ Voice preset applied:', ev.preset, ev.settings);
          break;
        case 'voice_effect_updated':
          // Clear current preset when user manually adjusts effects
          if (currentPreset) {
            setCurrentPreset(null);
            console.log('🔄 Preset cleared - user is using custom settings');
          }
          break;
        case 'error':
          setError(ev.message);
          setTimeout(() => setError(null), 5000); // Clear error after 5 seconds
          break;
        default:
          console.log('⚠️  Unknown event type:', ev.type);
      }
    };
    
    ws.addListener(onEvent); 
    ws.connect();
    
    // Auto-request songs when connected
    setTimeout(() => {
      if (ws.connected) {
        console.log('🔄 Auto-requesting songs list...');
        ws.send('refresh_songs');
      }
    }, 1000);
    
    return ()=>{ ws.removeListener(onEvent); };
  },[useMock, wsUrl]);

  React.useEffect(()=>{
    const v = videoRef.current; if (!v) return;
    const drift = Math.abs(v.currentTime - pos);
    if (drift > 0.1) v.currentTime = pos;
    if (playing && v.paused) v.play().catch(()=>{});
    if (!playing && !v.paused) v.pause();
  },[pos, playing]);

  // Discover audio devices using Python script
  const discoverAudioDevices = React.useCallback(async () => {
    try {
      console.log('🎤 Discovering audio devices via Python script...');
      
      // Call the Python devices server to get device list
      const response = await fetch('http://localhost:8766/api/devices');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const devices = await response.json();
      console.log('🎤 Received devices from Python script:', devices);
      
      // Transform the data to match our expected format
      const transformedDevices = {
        inputs: devices.inputs.map(device => ({
          deviceId: device.id, // Use the device ID from the backend
          label: device.name,
          channels: device.channels
        })),
        outputs: devices.outputs.map(device => ({
          deviceId: device.id, // Use the device ID from the backend
          label: device.name,
          channels: device.channels
        }))
      };
      
      setAudioDevices(transformedDevices);
      
      // Auto-select first available devices if none selected
      if (!selectedInput && transformedDevices.inputs.length > 0) {
        setSelectedInput(transformedDevices.inputs[0].deviceId);
      }
      if (!selectedOutput && transformedDevices.outputs.length > 0) {
        setSelectedOutput(transformedDevices.outputs[0].deviceId);
      }
      
      console.log('🎤 Successfully discovered audio devices:', { 
        inputs: transformedDevices.inputs.length, 
        outputs: transformedDevices.outputs.length 
      });
      
    } catch (error) {
      console.error('❌ Failed to get audio devices via Python script:', error);
      
      // Fallback devices on error
      const fallbackDevices = {
        inputs: [
          { deviceId: 'default', label: 'Default Microphone' },
          { deviceId: 'usb_mic', label: 'USB Microphone' },
          { deviceId: 'earpods', label: 'EarPods Microphone' }
        ],
        outputs: [
          { deviceId: 'default', label: 'Default Speakers' },
          { deviceId: 'usb_headphones', label: 'USB Headphones' },
          { deviceId: 'earpods', label: 'EarPods Speakers' }
        ]
      };
      
      setAudioDevices(fallbackDevices);
      
      if (!selectedInput && fallbackDevices.inputs.length > 0) {
        setSelectedInput(fallbackDevices.inputs[0].deviceId);
      }
      if (!selectedOutput && fallbackDevices.outputs.length > 0) {
        setSelectedOutput(fallbackDevices.outputs[0].deviceId);
      }
      
      console.log('🎤 Using fallback devices due to error');
    }
  }, [selectedInput, selectedOutput]);

  // Discover devices on mount
  React.useEffect(() => {
    discoverAudioDevices();
  }, [discoverAudioDevices]);

  // Debug video source changes and auto-start video
  React.useEffect(() => {
    console.log('🎬 Video source changed to:', videoSrc);
    if (videoSrc && videoRef.current) {
      console.log('🎥 Video element ready, source:', videoRef.current.src);
      
      // Auto-start video when source changes (3 second delay)
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.currentTime = 0;
          videoRef.current.play().catch(err => {
            console.log('🎬 Video autoplay failed:', err);
          });
        }
      }, 1600);
    }
  }, [videoSrc]);
  // Voice effect controls
  const voiceEffects = {
    autotune: { min: 0, max: 1, step: 0.1, default: 1.0 },
    pitchShift: { min: -12, max: 12, step: 1, default: 0 },
    voiceVolume: { min: 0.5, max: 2.0, step: 0.1, default: 1.1 },
    instrumentVolume: { min: 0.0, max: 2.0, step: 0.1, default: 2.0 }
  };

  // Voice presets
  const voicePresets = [
    { name: 'Natural', icon: '🎤', settings: { autotune: 0.3, pitchShift: 0, voiceVolume: 1.0, instrumentVolume: 2.0 } },
    { name: 'Autotune', icon: '🎵', settings: { autotune: 1.0, pitchShift: 0, voiceVolume: 1.1, instrumentVolume: 2.0 } },
    { name: 'Chipmunk', icon: '��️', settings: { autotune: 0.8, pitchShift: 7, voiceVolume: 1.2 } },
    { name: 'Deep Voice', icon: '��️', settings: { autotune: 0.6, pitchShift: -7, voiceVolume: 1.3 } },
    { name: 'Robot', icon: '🤖', settings: { autotune: 1.0, pitchShift: 0, voiceVolume: 1.0, chorus: true } },
    { name: 'Angelic', icon: '👼', settings: { autotune: 0.9, pitchShift: 2, voiceVolume: 1.4, reverb: true } }
  ];

  // Send voice effect changes
  function updateVoiceEffect(effect, value) {
    wsRef.current?.send('set_voice_effect', { effect, value });
  }

  // Apply voice preset
  function applyVoicePreset(preset) {
    setCurrentPreset(preset.name);
    wsRef.current?.send('set_voice_preset', { preset: preset.name });
  }

  const api = React.useMemo(()=> ({
    load_song:(id)=> {
      const payload = {
        songId: id,
        inputDevice: selectedInput,
        outputDevice: selectedOutput
      };
      return useMock ? window.__mock?.send('load_song', payload) : wsRef.current?.send(JSON.stringify({
        action: 'load_song',
        payload
      }));
    },
    start_session:()=> useMock?window.__mock?.send('start_session'):wsRef.current?.send(JSON.stringify({
      action: 'start_session'
    })),
    stop_session:()=> useMock?window.__mock?.send('stop_session'):wsRef.current?.send(JSON.stringify({
      action: 'stop_session'
    })),
    pause:()=> useMock?window.__mock?.send('pause'):wsRef.current?.send(JSON.stringify({
      action: 'pause'
    })),
    resume:()=> useMock?window.__mock?.send('resume'):wsRef.current?.send(JSON.stringify({
      action: 'resume'
    })),
    refresh_songs:()=> useMock?null:wsRef.current?.send(JSON.stringify({
      action: 'refresh_songs'
    })),
  }),[useMock, selectedInput, selectedOutput]);

  // Optional in-page mock (if toggled)
  React.useEffect(()=>{
    if (!useMock) { window.__mock = null; return; }
    const listeners = new Set();
    const mock = {
      playing:false, t0:0, offset:0, song:null,
      addListener:(cb)=>listeners.add(cb),
      emit:(e)=>listeners.forEach(l=>l(e)),
      send:(action,payload)=>{
        if (action==='load_song'){ mock.song={id:payload.songId, title:`Song ${payload.songId}`, durationSec:180}; mock.emit({type:'meta', song:mock.song}); mock.start(); }
        if (action==='start_session') mock.start();
        if (action==='stop_session') mock.stop();
        if (action==='pause') mock.pause();
        if (action==='resume') mock.resume();
      },
      start(){ mock.playing=true; mock.t0=performance.now()-mock.offset*1000; mock.tick(); mock.emit({type:'state',playing:true,positionSec:mock.pos()}); },
      stop(){ mock.playing=false; mock.offset=0; mock.emit({type:'state',playing:false,positionSec:0}); },
      pause(){ if(!mock.playing) return; mock.playing=false; mock.offset=mock.pos(); mock.emit({type:'state',playing:false,positionSec:mock.offset}); },
      resume(){ if(mock.playing) return; mock.start(); },
      pos(){ return mock.playing ? (performance.now()-mock.t0)/1000 : mock.offset; },
      tick(){ if(!mock.playing) return; const p=mock.pos(); mock.emit({type:'tick', positionSec:p}); requestAnimationFrame(()=>mock.tick()); }
    };
    window.__mock = mock;
    const onEvent = (ev)=>{
      if (ev.type==='state'){ setPlaying(ev.playing); setPos(ev.positionSec); }
      if (ev.type==='meta'){ setSong(ev.song); }
      if (ev.type==='tick'){ setPos(ev.positionSec); }
    };
    mock.addListener(onEvent);
    return ()=>{ window.__mock = null; };
  },[useMock]);

  const handleStartStop = ()=> playing ? api.stop_session() : api.start_session();
  const handlePauseResume = ()=> playing ? api.pause() : api.resume();
  const handleSelectSong = (s)=> {
    console.log('🎵 Selecting song:', s);
    console.log('🎬 Video source:', s.primaryVideo);
    
    api.load_song(s.id);
    
    // Set video source from backend data
    if (s.primaryVideo) {
      console.log('✅ Setting video source to:', s.primaryVideo);
      setVideoSrc(s.primaryVideo);
      
      // Start video after 3 seconds when song is selected
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.currentTime = 0;
          videoRef.current.play().catch(err => {
            console.log('🎬 Video autoplay failed:', err);
          });
        }
      }, 3000);
    } else {
      console.log('❌ No video source found for song');
    }
  };
  const handleRefreshSongs = ()=> api.refresh_songs();

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return e('div',{className:'w-full h-screen overflow-hidden text-neutral-900'},
    // Top config bar
    /*
    e('div',{className:'flex items-center justify-between px-4 py-2 border-b bg-white'},
      e('div',{className:'flex items-center gap-3'},
        e('label',{className:'flex items-center gap-2 text-sm'}, e('input',{type:'checkbox',checked:useMock,onChange:ev=>setUseMock(ev.target.checked)}),'Mock'),
        !useMock && e('div',{className:'flex items-center gap-2'},
          e('span',{className:'text-sm text-neutral-500'},'WS URL'),
          e('input',{className:'h-8 w-64 border rounded px-2', value:wsUrl, onChange:ev=>setWsUrl(ev.target.value)})
        )
      ),
      e('div',{className:'text-sm text-neutral-500'}, 
        song?`Loaded: ${song.title}`:'No song loaded', ' · ', 
        playing?'Playing':'Idle',' · ', 
        formatTime(pos)
      )
    ),
    */
    
    // Error banner
    error && e('div',{className:'bg-red-50 border-l-4 border-red-400 p-4 mx-4 mt-2'},
      e('div',{className:'flex'},
        e('div',{className:'flex-shrink-0'},
          e('svg',{className:'h-5 w-5 text-red-400',viewBox:'0 0 20 20',fill:'currentColor'},
            e('path',{fillRule:'evenodd',d:'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z',clipRule:'evenodd'})
          )
        ),
        e('div',{className:'ml-3'},
          e('p',{className:'text-sm text-red-700'}, error)
        )
      )
    ),
    
    // Grid main
    e('div',{className:'h-[calc(100vh-44px)] grid', style:{gridTemplateColumns: sidebarOpen? `${sidebarWidth}px 12px 1fr` : '0px 0px 1fr'}},
      // Sidebar
      e('aside',{className:'overflow-hidden border-r bg-white'},
        e('div',{className:'p-3 flex items-center justify-between border-b'},
          e('button',{className:'rounded px-2 py-1 hover:bg-neutral-100', onClick:()=>setSidebarOpen(v=>!v)}, sidebarOpen?'⨯':'≡'),
          e('div',{className:'flex items-center gap-2'},
            e('span',{className:'font-medium'},'Songs'),
            e('button',{className:'text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200', onClick:handleRefreshSongs}, '🔄')
          )
        ),
        e('div',{className:'p-2 h-full overflow-auto'},
          songs.length === 0 ? 
            e('div',{className:'text-center text-neutral-500 py-8'}, 
              e('div',{className:'text-2xl mb-2'}, '🎵'),
              e('div',{className:'text-sm'}, 'No songs found'),
              e('div',{className:'text-xs mt-1'}, 'Check autotune-app/songs/ directory')
            ) :
            e('div',{className:'flex flex-col gap-1'},
              songs.map(s=> e('button',{
                key:s.id, 
                className:`text-left rounded px-2 py-2 hover:bg-neutral-100 border-l-4 ${
                  song?.id === s.id ? 'border-blue-500 bg-blue-50' : 'border-transparent'
                }`, 
                onClick:()=>handleSelectSong(s)
              }, 
                e('div',{className:'font-medium'}, s.title),
                e('div',{className:'text-xs text-neutral-500 mt-1'},
                  s.hasMelody ? '🎼' : '⚠️', ' Melody ',
                  s.hasInstrumental ? '🎸' : '⚠️', ' Instrumental'
                )
              ))
            )
        )
      ),
      
      // Resize handle
      e('div',{onMouseDown:(ev)=>{ev.preventDefault(); const move=(e)=>{ const w=Math.max(220, Math.min(520, e.clientX)); setSidebarWidth(w); }; const up=()=>{window.removeEventListener('mousemove',move);window.removeEventListener('mouseup',up);}; window.addEventListener('mousemove',move);window.addEventListener('mouseup',up);} , className: sidebarOpen?'cursor-col-resize bg-neutral-200':'bg-transparent'}),
      
      // Main content
      e('main',{className:'h-full p-4 overflow-hidden'},
        // Controls
        e('div',{className:'mb-4'},
          e('div',{className:'shadow-sm border rounded-xl bg-white'},
            e('div',{className:'py-3 px-4 flex items-center gap-3'},
              e('button',{onClick:handleStartStop, className:'rounded-2xl px-3 py-2 bg-neutral-900 text-white'}, '♦ ', playing?'Stop Session':'Start Session'),
              e('button',{onClick:handlePauseResume, className:'rounded-full px-3 py-2 border'}, playing?'◯ Pause':'▶ Resume')
            )
          )
        ),
        
        // Autotune Status
        e('div',{className:'mb-4'},
          e('div',{className:'shadow-sm border rounded-xl bg-white'},
            e('div',{className:'py-3 px-4'},
              e('div',{className:'flex items-center gap-3 mb-2'},
                e('span',{className:'font-medium'}, '🎤 Autotune Status'),
                e('span',{className:'text-sm text-neutral-500'}, 'Professional real-time pitch correction')
              ),
              e('div',{className:'grid grid-cols-3 gap-4 text-sm'},
                e('div',{className:'text-center p-2 bg-green-50 rounded'},
                  e('div',{className:'font-medium text-green-700'}, 'Noise Suppression'),
                  e('div',{className:'text-green-600'}, 'Active')
                ),
                e('div',{className:'text-center p-2 bg-blue-50 rounded'},
                  e('div',{className:'font-medium text-blue-700'}, 'Pitch Detection'),
                  e('div',{className:'text-green-600'}, 'Real-time')
                ),
                e('div',{className:'text-center p-2 bg-purple-50 rounded'},
                  e('div',{className:'font-medium text-purple-700'}, 'Autotune'),
                  e('div',{className:'text-green-600'}, 'Melody Map')
                )
              )
            )
          )
        ),
        
        // Voice Effects
        e('div',{className:'mb-4'},
          e('div',{className:'shadow-sm border rounded-xl bg-white'},
            e('div',{className:'py-3 px-4'},
              e('div',{className:'flex items-center gap-3 mb-3'},
                e('span',{className:'font-medium'}, '🎛️ Voice Effects'),
                e('span',{className:'text-sm text-neutral-500'}, 'Real-time voice modification')
              ),
              
              // Voice Effect Sliders
              e('div',{className:'grid grid-cols-4 gap-4 mb-4'},
                e('div',{className:'flex flex-col gap-2'},
                  e('label',{className:'text-sm font-medium text-neutral-700'}, 'Autotune Strength'),
                  e('input',{
                    type: 'range',
                    min: voiceEffects.autotune.min,
                    max: voiceEffects.autotune.max,
                    step: voiceEffects.autotune.step,
                    defaultValue: voiceEffects.autotune.default,
                    onChange: (ev) => updateVoiceEffect('autotune', parseFloat(ev.target.value)),
                    className: 'w-full'
                  }),
                  e('div',{className:'text-xs text-neutral-500 text-center'}, 
                    voiceEffects.autotune.default
                  )
                ),
                e('div',{className:'flex flex-col gap-2'},
                  e('label',{className:'text-sm font-medium text-neutral-700'}, 'Pitch Shift'),
                  e('input',{
                    type: 'range',
                    min: voiceEffects.pitchShift.min,
                    max: voiceEffects.pitchShift.max,
                    step: voiceEffects.pitchShift.step,
                    defaultValue: voiceEffects.pitchShift.default,
                    onChange: (ev) => updateVoiceEffect('pitch_shift', parseInt(ev.target.value)),
                    className: 'w-full'
                  }),
                  e('div',{className:'text-xs text-neutral-500 text-center'}, 
                    voiceEffects.pitchShift.default + ' semitones'
                  )
                ),
                e('div',{className:'flex flex-col gap-2'},
                  e('label',{className:'text-sm font-medium text-neutral-700'}, 'Voice Volume'),
                  e('input',{
                    type: 'range',
                    min: voiceEffects.voiceVolume.min,
                    max: voiceEffects.voiceVolume.max,
                    step: voiceEffects.voiceVolume.step,
                    defaultValue: voiceEffects.voiceVolume.default,
                    onChange: (ev) => updateVoiceEffect('voice_volume', parseFloat(ev.target.value)),
                    className: 'w-full'
                  }),
                  e('div',{className:'text-xs text-neutral-500 text-center'}, 
                    voiceEffects.voiceVolume.default + 'x'
                  )
                ),
                e('div',{className:'flex flex-col gap-2'},
                  e('label',{className:'text-sm font-medium text-neutral-700'}, 'Instrument Volume'),
                  e('input',{
                    type: 'range',
                    min: voiceEffects.instrumentVolume.min,
                    max: voiceEffects.instrumentVolume.max,
                    step: voiceEffects.instrumentVolume.step,
                    defaultValue: voiceEffects.instrumentVolume.default,
                    onChange: (ev) => updateVoiceEffect('instrument_volume', parseFloat(ev.target.value)),
                    className: 'w-full'
                  }),
                  e('div',{className:'text-xs text-neutral-500 text-center'}, 
                    voiceEffects.instrumentVolume.default + 'x'
                  )
                )
              ),
              
              // Voice Presets
              e('div',{className:'mb-3'},
                e('div',{className:'text-sm font-medium text-neutral-700 mb-2'}, 'Quick Presets:'),
                e('div',{className:'flex flex-wrap gap-2'},
                  // Custom mode indicator
                  e('button',{
                    key: 'custom',
                    onClick: () => {
                      setCurrentPreset(null);
                      // Reset to default values
                      updateVoiceEffect('autotune', voiceEffects.autotune.default);
                      updateVoiceEffect('pitch_shift', voiceEffects.pitchShift.default);
                      updateVoiceEffect('voice_volume', voiceEffects.voiceVolume.default);
                      updateVoiceEffect('instrument_volume', voiceEffects.instrumentVolume.default);
                    },
                    className: `px-3 py-1 text-xs rounded-full border transition-colors ${
                      currentPreset === null 
                        ? 'bg-green-500 text-white border-green-500 shadow-md' 
                        : 'hover:bg-neutral-50 border-neutral-300'
                    }`
                  }, 
                    '⚙️ Custom'
                  ),
                  // Preset buttons
                  voicePresets.map(preset => 
                    e('button',{
                      key: preset.name,
                      onClick: () => applyVoicePreset(preset),
                      className: `px-3 py-1 text-xs rounded-full border transition-colors ${
                        currentPreset === preset.name 
                          ? 'bg-blue-500 text-white border-blue-500 shadow-md' 
                          : 'hover:bg-neutral-50 border-neutral-300'
                      }`
                    }, 
                      preset.icon + ' ' + preset.name
                    )
                  )
                )
              ),
              
              e('div',{className:'text-xs text-neutral-500'},
                'Voice effects are applied in real-time by the C++ backend'
              )
            )
          )
        ),
        
        // Video
        e('div',{className:'shadow-sm border rounded-xl bg-white h-[calc(70%-2rem)] min-h-[200px]'},
          e('div',{className:'h-full p-2'},
            e('div',{className:'w-full h-full rounded-xl bg-black/90 flex items-center justify-center overflow-hidden relative'},
              e('video',{
                ref: videoRef, 
                className: 'w-full h-full object-contain', 
                playsInline: true, 
                muted: true,
                controls: false,
                preload: 'metadata',
                crossOrigin: 'anonymous'
              },
                videoSrc ? e('source', {src: videoSrc, type: 'video/mp4'}) : null
              ),
              !videoSrc && e('div',{className:'absolute text-white/70 text-lg'}, '🎵 Select a song to load video')
            )
          )
        ),
        
        // Audio Device Selection
        e('div',{className:'mt-4'},
          e('div',{className:'shadow-sm border rounded-xl bg-white'},
            e('div',{className:'py-3 px-4'},
              e('div',{className:'flex items-center gap-3 mb-3'},
                e('span',{className:'font-medium'}, '🎤 Audio Devices'),
                e('button',{
                  onClick: discoverAudioDevices,
                  className: 'text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200'
                }, '🔄 Refresh')
              ),
              e('div',{className:'grid grid-cols-2 gap-4 text-sm'},
                e('div',{className:'flex flex-col gap-2'},
                  e('label',{className:'text-sm font-medium text-neutral-700'}, 'Microphone Input:'),
                  e('select',{
                    value: selectedInput,
                    onChange: (ev) => setSelectedInput(ev.target.value),
                    className: 'border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
                  }, 
                    audioDevices.inputs?.map(device => 
                      e('option',{key: device.deviceId, value: device.deviceId}, 
                        device.label || `Microphone ${device.deviceId.slice(0, 8)}...`
                      )
                    ) || e('option',{value: ''}, 'No input devices found')
                  )
                ),
                e('div',{className:'flex flex-col gap-2'},
                  e('label',{className:'text-sm font-medium text-neutral-700'}, 'Speaker Output:'),
                  e('select',{
                    value: selectedOutput,
                    onChange: (ev) => setSelectedOutput(ev.target.value),
                    className: 'border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
                  },
                    audioDevices.outputs?.map(device => 
                      e('option',{key: device.deviceId, value: device.deviceId}, 
                        device.label || `Speaker ${device.deviceId.slice(0, 8)}...`
                      )
                    ) || e('option',{value: ''}, 'No output devices found')
                  )
                )
              ),
              e('div',{className:'mt-3 text-xs text-neutral-500'},
                'Selected devices will be sent to the C++ backend when loading songs'
              )
            )
          )
        ),
        
        // C++ Waveform Integration
        /*
        e('div',{className:'mt-4'},
          e('div',{className:'shadow-sm border rounded-xl bg-white'},
            e('div',{className:'p-2 relative h-44 rounded-xl overflow-hidden'},
              e('div',{className:'h-full flex items-center justify-center bg-gradient-to-r from-blue-50 to-purple-50'},
                e('div',{className:'text-center text-neutral-600'},
                  e('div',{className:'text-2xl mb-2'}, '🎤'),
                  e('div',{className:'font-medium'}, 'C++ Autotune Visualization'),
                  e('div',{className:'text-sm mt-1'}, 'Real-time pitch correction display'),
                  e('div',{className:'text-xs mt-2 text-neutral-500'}, 'Opens in separate window when session starts')
                )
              ),
              e('div',{className:'absolute top-2 right-3 text-xs bg-black/50 text-white px-2 py-1 rounded-full'},
                e('span',{className:'mr-3'}, e('span',{className:'inline-block w-2 h-2 rounded-full bg-green-500 mr-1'}),'Your voice (green)'),
                e('span',null, e('span',{className:'inline-block w-2 h-2 rounded-full bg-red-500 mr-1'}),'Your voice (green)'),
                e('span',null, e('span',{className:'inline-block w-2 h-2 rounded-full bg-red-500 mr-1'}),'Target melody (red)')
              )
            )
          )
        )
        */
      )
    )
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(App));
