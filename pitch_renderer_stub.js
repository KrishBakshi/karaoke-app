// Replace this with your real WASM/Node-API renderer.
// Expected to export an async function:
export async function initPitchRenderer({ canvas, onReady, onDispose }) {
  const ctx = canvas.getContext('2d');
  let running = true, t = 0;
  const draw = () => {
    if (!running) return;
    const w = canvas.width = canvas.clientWidth;
    const h = canvas.height = canvas.clientHeight;
    ctx.clearRect(0,0,w,h);
    ctx.globalAlpha = 1;
    ctx.fillStyle = '#0b0b0b'; ctx.fillRect(0,0,w,h);
    // Red line (song pitch, mock)
    ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 2; ctx.beginPath();
    for (let x=0;x<w;x++){ const y = h/2 + Math.sin((x+t)/50)*18; x?ctx.lineTo(x,y):ctx.moveTo(x,y); } ctx.stroke();
    // Green line (live voice, mock)
    ctx.strokeStyle = '#22c55e'; ctx.beginPath();
    for (let x=0;x<w;x++){ const y = h/2 + Math.sin((x+t*1.2)/33)*30; x?ctx.lineTo(x,y):ctx.moveTo(x,y); } ctx.stroke();
    t += 2; requestAnimationFrame(draw);
  };
  draw();
  onReady?.();
  return () => { running = false; onDispose?.(); };
}
