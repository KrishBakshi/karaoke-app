// Minimal WebSocket mock backend for the karaoke frontend
// Usage: npm i ws && node mock_backend_server.js

const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8765 });

console.log('🎧 Mock backend WS listening on ws://localhost:8765');

wss.on('connection', (ws) => {
  console.log('Client connected');
  let playing = false;
  let t0 = 0;
  let offset = 0;
  let currentSong = null;
  let raf = null;

  function position(){ return playing ? (Date.now() - t0)/1000 : offset; }

  function broadcast(ev){
    try { ws.send(JSON.stringify(ev)); } catch {}
  }

  function start(){
    playing = true;
    t0 = Date.now() - offset*1000;
    tick();
    broadcast({ type:'state', playing, positionSec: position() });
  }
  function stop(){
    playing = false; offset = 0;
    if (raf) { clearImmediate(raf); raf = null; }
    broadcast({ type:'state', playing, positionSec: 0 });
  }
  function pause(){ if (!playing) return; playing=false; offset = position(); broadcast({ type:'state', playing, positionSec: offset }); }
  function resume(){ if (playing) return; start(); }

  function tick(){
    if (!playing) return;
    broadcast({ type:'tick', positionSec: position() });
    raf = setImmediate(tick);
  }

  ws.on('message', (raw) => {
    let msg = {}; try { msg = JSON.parse(raw.toString()); } catch {}
    const { action, payload } = msg;
    if (action === 'load_song') {
      const id = payload?.songId || '1';
      currentSong = { id, title: `Demo Song ${id}`, durationSec: 180 };
      broadcast({ type:'meta', song: currentSong });
      start(); // auto-start after load
    }
    if (action === 'start_session') start();
    if (action === 'stop_session') stop();
    if (action === 'pause') pause();
    if (action === 'resume') resume();
  });

  ws.on('close', () => {
    if (raf) clearImmediate(raf);
    console.log('Client disconnected');
  });
});
