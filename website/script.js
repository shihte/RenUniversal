// Boids flocking simulation for RenUniversal background canvas
const canvas = document.getElementById('bg-canvas');
const ctx = canvas.getContext('2d');
let W, H;

function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = document.documentElement.scrollHeight || window.innerHeight;
}
resize();
window.addEventListener('resize', () => { resize(); });

// Boid class
class Boid {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.vx = (Math.random() - 0.5) * 3;
        this.vy = (Math.random() - 0.5) * 3;
        this.maxSpeed = 2.5;
        this.maxForce = 0.05;
        this.size = 5;
        this.history = [];
        this.maxHistory = 10;
        
        // Google I/O 2026 Palette (high opacity for brightness)
        const colors = [
            'rgba(66, 133, 244, 0.75)',  // Google Blue
            'rgba(52, 168, 83, 0.75)',   // Google Green
            'rgba(251, 188, 5, 0.75)',   // Google Yellow
            'rgba(234, 67, 53, 0.75)',   // Google Red
            'rgba(124, 58, 255, 0.75)',  // Violet
            'rgba(255, 110, 0, 0.75)'    // Orange
        ];
        this.color = colors[Math.floor(Math.random() * colors.length)];
    }

    update() {
        // Record trail history
        this.history.push({ x: this.x, y: this.y });
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        }

        this.x += this.vx;
        this.y += this.vy;

        // Wrap around screen boundaries & clear history to prevent screen-crossing trail lines
        if (this.x < 0) { this.x = W; this.history = []; }
        if (this.x > W) { this.x = 0; this.history = []; }
        if (this.y < 0) { this.y = H; this.history = []; }
        if (this.y > H) { this.y = 0; this.history = []; }
    }

    // Reynolds flocking behavior
    flock(boids) {
        let sep = this.separate(boids);
        let ali = this.align(boids);
        let coh = this.cohere(boids);

        // Weights
        sep.x *= 1.5; sep.y *= 1.5;
        ali.x *= 1.0; ali.y *= 1.0;
        coh.x *= 1.0; coh.y *= 1.0;

        this.vx += sep.x + ali.x + coh.x;
        this.vy += sep.y + ali.y + coh.y;

        // Limit speed
        const speed = Math.sqrt(this.vx * this.vx + this.vy * this.vy);
        if (speed > this.maxSpeed) {
            this.vx = (this.vx / speed) * this.maxSpeed;
            this.vy = (this.vy / speed) * this.maxSpeed;
        }
    }

    separate(boids) {
        let steer = { x: 0, y: 0 };
        let count = 0;
        const desiredSeparation = 25;

        for (let other of boids) {
            let d = this.dist(this.x, this.y, other.x, other.y);
            if (other !== this && d > 0 && d < desiredSeparation) {
                let diff = { x: this.x - other.x, y: this.y - other.y };
                // Scale by distance (closer = stronger push)
                diff.x /= d;
                diff.y /= d;
                steer.x += diff.x;
                steer.y += diff.y;
                count++;
            }
        }
        if (count > 0) {
            steer.x /= count;
            steer.y /= count;
        }
        return steer;
    }

    align(boids) {
        let sum = { x: 0, y: 0 };
        let count = 0;
        const neighborDist = 50;

        for (let other of boids) {
            let d = this.dist(this.x, this.y, other.x, other.y);
            if (other !== this && d > 0 && d < neighborDist) {
                sum.x += other.vx;
                sum.y += other.vy;
                count++;
            }
        }
        if (count > 0) {
            sum.x /= count;
            sum.y /= count;
            let steer = { x: sum.x - this.vx, y: sum.y - this.vy };
            // Limit steering force
            const force = Math.sqrt(steer.x * steer.x + steer.y * steer.y);
            if (force > this.maxForce) {
                steer.x = (steer.x / force) * this.maxForce;
                steer.y = (steer.y / force) * this.maxForce;
            }
            return steer;
        }
        return { x: 0, y: 0 };
    }

    cohere(boids) {
        let sum = { x: 0, y: 0 };
        let count = 0;
        const neighborDist = 50;

        for (let other of boids) {
            let d = this.dist(this.x, this.y, other.x, other.y);
            if (other !== this && d > 0 && d < neighborDist) {
                sum.x += other.x;
                sum.y += other.y;
                count++;
            }
        }
        if (count > 0) {
            sum.x /= count;
            sum.y /= count;
            let desired = { x: sum.x - this.x, y: sum.y - this.y };
            let steer = { x: desired.x - this.vx, y: desired.y - this.vy };
            const force = Math.sqrt(steer.x * steer.x + steer.y * steer.y);
            if (force > this.maxForce) {
                steer.x = (steer.x / force) * this.maxForce;
                steer.y = (steer.y / force) * this.maxForce;
            }
            return steer;
        }
        return { x: 0, y: 0 };
    }

    dist(x1, y1, x2, y2) {
        const dx = x1 - x2;
        const dy = y1 - y2;
        return Math.sqrt(dx * dx + dy * dy);
    }

    draw() {
        // 1. Draw subtle trails
        for (let i = 0; i < this.history.length; i++) {
            const pos = this.history[i];
            const ratio = (i + 1) / this.history.length;
            ctx.save();
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, this.size * 0.7 * ratio, 0, Math.PI * 2);
            // Replace alpha parameter in rgba for progressive fading
            ctx.fillStyle = this.color.replace('0.75', (0.15 * ratio).toString());
            ctx.fill();
            ctx.restore();
        }

        // 2. Draw glowing circular head
        ctx.save();
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        
        // Bright glow effect using shadow properties
        ctx.shadowBlur = 10;
        ctx.shadowColor = this.color;
        
        ctx.fill();
        ctx.restore();
    }
}

// Initialize boids
const boids = [];
const numBoids = Math.min(140, Math.floor((window.innerWidth * window.innerHeight) / 10000));
for (let i = 0; i < numBoids; i++) {
    boids.push(new Boid(Math.random() * W, Math.random() * H));
}

// Keep the skeleton animation as background poses
const PTS = [
    {x:.5,y:.042},{x:.5,y:.082},{x:.37,y:.11},{x:.63,y:.11},
    {x:.28,y:.16},{x:.72,y:.16},{x:.23,y:.21},{x:.77,y:.21},
    {x:.5,y:.165},{x:.42,y:.23},{x:.58,y:.23},
    {x:.41,y:.305},{x:.59,y:.305},{x:.40,y:.38},{x:.60,y:.38}
];
const CONN = [
    [0,1],[1,2],[1,3],[2,3],[2,4],[4,6],[3,5],[5,7],
    [1,8],[8,9],[8,10],[9,10],[9,11],[11,13],[10,12],[12,14]
];
const SKELETONS = [
    {cx:.12,cy:.12,sc:.10,op:.08,ph:0,   c:[0,212,255]},
    {cx:.88,cy:.09,sc:.09,op:.07,ph:1.3, c:[124,58,255]},
    {cx:.04,cy:.52,sc:.08,op:.06,ph:2.5, c:[0,212,255]},
    {cx:.93,cy:.45,sc:.09,op:.06,ph:.8,  c:[124,58,255]},
    {cx:.50,cy:.78,sc:.11,op:.05,ph:1.9, c:[0,212,255]},
];
let t = 0;

function drawSkeleton(s) {
    const {cx,cy,sc,op,ph,c} = s;
    const br = 1 + Math.sin(t*.7+ph)*.025;
    const dx = Math.sin(t*.25+ph)*.008;
    const dy = Math.cos(t*.33+ph*1.2)*.004;
    const pts = PTS.map(p => ({
        x:(cx+dx+(p.x-.5)*sc*br)*W,
        y:(cy+dy+(p.y-.18)*sc*2.2*br)*H
    }));
    ctx.lineWidth = .8;
    for(const [a,b] of CONN){
        ctx.strokeStyle = `rgba(${c},${op*.75})`;
        ctx.beginPath();
        ctx.moveTo(pts[a].x,pts[a].y);
        ctx.lineTo(pts[b].x,pts[b].y);
        ctx.stroke();
    }
    for(let i=0;i<pts.length;i++){
        const pulse = 1 + Math.sin(t*1.1+i*.4+ph)*.15;
        const r = (i===0?2.8:1.8)*pulse;
        ctx.beginPath();
        ctx.arc(pts[i].x,pts[i].y,r,0,Math.PI*2);
        ctx.fillStyle = `rgba(${c},${op*1.6})`;
        ctx.fill();
    }
}

function frame() {
    ctx.clearRect(0, 0, W, H);
    
    // Draw skeletons
    t += .008;
    SKELETONS.forEach(drawSkeleton);
    
    // Draw and update boids (Temporarily commented out)
    /*
    for (let boid of boids) {
        boid.flock(boids);
        boid.update();
        boid.draw();
    }

    // Connect nearby boids with thin constellation lines
    ctx.lineWidth = 0.5;
    for (let i = 0; i < boids.length; i++) {
        for (let j = i + 1; j < boids.length; j++) {
            const dx = boids[i].x - boids[j].x;
            const dy = boids[i].y - boids[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 110) {
                const alpha = (1 - dist / 110) * 0.15;
                ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
                ctx.beginPath();
                ctx.moveTo(boids[i].x, boids[i].y);
                ctx.lineTo(boids[j].x, boids[j].y);
                ctx.stroke();
            }
        }
    }
    */

    requestAnimationFrame(frame);
}
frame();

// Nav background toggle on scroll
const nav = document.getElementById('nav');
if (nav) {
    window.addEventListener('scroll', () => {
        nav.classList.toggle('nav-scrolled', window.scrollY > 40);
    });
}

// ─── Organic background drift for .hero-brand-title ───────────────────────
// Smooth random drift: perlin-like multi-octave sinusoids → no jerkiness
(function () {
    const els = document.querySelectorAll('.hero-brand-title');
    if (!els.length) return;

    // Each axis is driven by a sum of slow sinusoids with irrational ratios
    // so they never repeat exactly — organic & smooth, zero easing dead-zones
    let t = 0;
    const seeds = [
        { ax: 0.37, bx: 0.13, cx: 0.71,  ay: 0.41, by: 0.17, cy: 0.53 },
        { ax: 0.23, bx: 0.59, cx: 0.11,  ay: 0.67, by: 0.29, cy: 0.43 },
        { ax: 0.61, bx: 0.07, cx: 0.83,  ay: 0.19, by: 0.73, cy: 0.31 },
    ];

    function tick() {
        t += 0.003; // speed: smaller = slower drift, no linear ticks
        els.forEach((el, i) => {
            const s = seeds[i % seeds.length];
            // Combine 3 sine waves per axis → smooth but never periodic
            const x = (Math.sin(t * s.ax * 2.1) * 0.4
                     + Math.sin(t * s.bx * 1.3) * 0.35
                     + Math.sin(t * s.cx * 0.7) * 0.25 + 1) / 2 * 100;
            const y = (Math.sin(t * s.ay * 1.7) * 0.4
                     + Math.sin(t * s.by * 2.3) * 0.35
                     + Math.sin(t * s.cy * 0.9) * 0.25 + 1) / 2 * 100;
            el.style.backgroundPosition = `${x.toFixed(2)}% ${y.toFixed(2)}%`;
        });
        requestAnimationFrame(tick);
    }
    tick();
})();
