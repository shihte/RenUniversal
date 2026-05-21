const fs = require('fs');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;

const html = fs.readFileSync('web/camera.html', 'utf-8');
const dom = new JSDOM(html, { url: "http://127.0.0.1:8080/camera" });
const window = dom.window;
const document = window.document;

const data = {
    connected: true,
    fps: 30,
    ratio: 50,
    latency_ms: 20,
    active_events: {},
    active_skills: {},
    metrics: {},
    trigger_counts: {},
    local_ip: "192.168.1.100",
    public_url: null,
    camera_source: "local_0",
    flip_enabled: true,
    is_active: true
};

const statusEl = document.getElementById('connection-status');
const liveIndicator = document.getElementById('live-indicator');
const toggleEl = document.getElementById('detection-toggle');

try {
    const colorClass = data.connected ? 'bg-green-500' : 'bg-red-500';
    if (statusEl) if (statusEl) statusEl.className = `w-3 h-3 rounded-full animate-pulse ${colorClass}`;
    if (liveIndicator) if (liveIndicator) liveIndicator.className = `w-2 h-2 rounded-full ${colorClass}`;

    const fpsEl = document.getElementById('fps-display'); if (fpsEl) fpsEl.textContent = `FPS: ${data.fps}`;
    const ratioEl = document.getElementById('ratio-value'); if (ratioEl) ratioEl.textContent = `${data.ratio}%`;
    const latencyEl = document.getElementById('latency-value'); if (latencyEl) latencyEl.textContent = `${data.latency_ms}ms`;
    
    // ... all the way to localLinkEl
    const tunnelContainer = document.getElementById('tunnel-info-container');
    if (tunnelContainer) {
        const localIp = data.local_ip || '127.0.0.1';
        const localMobileUrl = `http://${localIp}:8080/mobile`;
        
        const localLinkEl = document.getElementById('local-link');
        console.log("localLinkEl before:", localLinkEl ? localLinkEl.href : "null");
        if (localLinkEl && localLinkEl.href !== localMobileUrl) {
            localLinkEl.href = localMobileUrl;
            localLinkEl.textContent = localMobileUrl;
            document.getElementById('local-qr').src = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(localMobileUrl)}`;
            console.log("Updated localLinkEl:", localLinkEl.href);
        }
        
        console.log("public_url is", data.public_url);
    }
} catch (e) {
    console.error("Crash!", e);
}
