import Foundation

struct BundledGames {
    static let flappyBirdHtml = """
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
      body { margin: 0; padding: 0; background: #87CEEB; overflow: hidden; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; }
      canvas { background: #70c5ce; display: block; border: 4px solid #fff; border-radius: 8px; box-shadow: 0 10px 20px rgba(0,0,0,0.5); max-width: 100%; max-height: 80vh; object-fit: contain; }
      #info { margin-bottom: 20px; color: white; font-family: sans-serif; font-weight: bold; font-size: 24px; text-shadow: 2px 2px 0 #000; }
    </style>
    </head>
    <body>
    <div id="info">CTAR TUCK: <span id="status" style="color:red">IDLE</span></div>
    <canvas id="game" width="400" height="600"></canvas>
    <script>
    const canvas = document.getElementById('game');
    const ctx = canvas.getContext('2d');
    
    let frames = 0;
    let score = 0;
    let state = 'START'; // START, PLAY, OVER
    let pipes = [];
    
    let bird = {
      x: 100, y: 300, w: 34, h: 24,
      velocity: 0, gravity: 0.6, jump: -8,
      draw: function() {
        ctx.fillStyle = '#FF0';
        ctx.beginPath();
        ctx.arc(this.x, this.y, 15, 0, Math.PI*2);
        ctx.fill();
        ctx.stroke();
      },
      update: function() {
        this.velocity += this.gravity;
        this.y += this.velocity;
        if (this.y >= canvas.height - 20) {
          this.y = canvas.height - 20;
          state = 'OVER';
        }
      },
      flap: function() {
        this.velocity = this.jump;
      }
    };
    
    function drawPipes() {
      for(let i=0; i<pipes.length; i++) {
        let p = pipes[i];
        ctx.fillStyle = '#2ecc71';
        // top pipe
        ctx.fillRect(p.x, 0, p.w, p.top);
        // bottom pipe
        ctx.fillRect(p.x, canvas.height - p.bottom, p.w, p.bottom);
      }
    }
    
    function updatePipes() {
      if(frames % 100 === 0) {
        let gap = 150;
        let top = Math.max(50, Math.random() * (canvas.height - gap - 100));
        pipes.push({ x: canvas.width, w: 50, top: top, bottom: canvas.height - gap - top, passed: false });
      }
      for(let i=0; i<pipes.length; i++) {
        let p = pipes[i];
        p.x -= 3;
        
        // collision
        if(bird.x + 15 > p.x && bird.x - 15 < p.x + p.w) {
          if(bird.y - 15 < p.top || bird.y + 15 > canvas.height - p.bottom) {
            state = 'OVER';
          }
        }
        // score
        if(p.x + p.w < bird.x && !p.passed) {
          score++;
          p.passed = true;
        }
      }
      pipes = pipes.filter(p => p.x > -p.w);
    }
    
    function draw() {
      ctx.clearRect(0,0,canvas.width,canvas.height);
      bird.draw();
      drawPipes();
      
      ctx.fillStyle = '#FFF';
      ctx.font = '30px sans-serif';
      if(state === 'START') {
        ctx.fillText("Tuck Chin to Start", 80, 200);
      } else if (state === 'OVER') {
        ctx.fillText("Game Over", 130, 200);
        ctx.fillText("Score: " + score, 150, 250);
        ctx.fillText("Tuck Chin to Restart", 70, 300);
      } else {
        ctx.fillText(score, canvas.width/2 - 10, 50);
      }
    }
    
    function update() {
      if(state === 'PLAY') {
        bird.update();
        updatePipes();
      }
    }
    
    function loop() {
      update();
      draw();
      frames++;
      requestAnimationFrame(loop);
    }
    
    let wasTucked = false;
    
    function onFlap() {
        if(state === 'START') {
            state = 'PLAY';
            bird.flap();
        } else if (state === 'PLAY') {
            bird.flap();
        } else if (state === 'OVER') {
            pipes = [];
            score = 0;
            bird.y = 300;
            bird.velocity = 0;
            state = 'START';
        }
    }
    
    window.updatePostureData = function(jsonStr) {
      try {
          let data = JSON.parse(jsonStr);
          let isTucked = data.active_triggers && data.active_triggers['ctar_tuck'] === true;
          
          if(isTucked && !wasTucked) {
              onFlap();
          }
          wasTucked = isTucked;
          
          let stat = document.getElementById('status');
          stat.innerText = isTucked ? "TUCKED" : "IDLE";
          stat.style.color = isTucked ? "#0f0" : "red";
      } catch(e) {}
    }
    
    // Fallback spacebar for testing on web
    window.addEventListener('keydown', (e) => {
        if(e.code === 'Space') onFlap();
    });
    
    // Fallback touch for testing on mobile
    window.addEventListener('touchstart', (e) => {
        onFlap();
    });
    
    loop();
    </script>
    </body>
    </html>
    """
    
    static let dinoHtml = """
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
      body { margin: 0; padding: 0; background: #fff; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; overflow: hidden; font-family: 'Courier New', Courier, monospace; }
      canvas { border-bottom: 2px solid #535353; max-width: 100%; max-height: 30vh; object-fit: contain;}
      #info { margin-bottom: 20px; color: #535353; font-weight: bold; font-size: 24px; }
    </style>
    </head>
    <body>
    <div id="info">CTAR TUCK: <span id="status" style="color:red">IDLE</span></div>
    <canvas id="game" width="600" height="200"></canvas>
    <script>
    const canvas = document.getElementById('game');
    const ctx = canvas.getContext('2d');
    
    let state = 'START';
    let frames = 0;
    let score = 0;
    let obstacles = [];
    
    let dino = {
      x: 50, y: 150, w: 40, h: 40,
      velocity: 0, gravity: 0.8, jump: -12,
      isGrounded: true,
      draw: function() {
        ctx.fillStyle = '#535353';
        ctx.fillRect(this.x, this.y, this.w, this.h);
      },
      update: function() {
        this.velocity += this.gravity;
        this.y += this.velocity;
        if(this.y >= 150) {
          this.y = 150;
          this.velocity = 0;
          this.isGrounded = true;
        } else {
          this.isGrounded = false;
        }
      },
      jumpAction: function() {
        if(this.isGrounded) {
          this.velocity = this.jump;
          this.isGrounded = false;
        }
      }
    };
    
    function updateObstacles() {
      if(frames % 80 === 0 && Math.random() > 0.3) {
        obstacles.push({ x: canvas.width, y: 150, w: 20, h: 40 });
      }
      for(let i=0; i<obstacles.length; i++) {
        let obs = obstacles[i];
        obs.x -= 6;
        
        // collision
        if(dino.x < obs.x + obs.w && dino.x + dino.w > obs.x &&
           dino.y < obs.y + obs.h && dino.y + dino.h > obs.y) {
           state = 'OVER';
        }
      }
      obstacles = obstacles.filter(o => o.x > -50);
      if(frames % 10 === 0 && state === 'PLAY') score++;
    }
    
    function draw() {
      ctx.clearRect(0,0,canvas.width,canvas.height);
      dino.draw();
      ctx.fillStyle = '#535353';
      for(let o of obstacles) {
        ctx.fillRect(o.x, o.y, o.w, o.h);
      }
      
      ctx.font = '20px Courier';
      if(state === 'START') {
        ctx.fillText("Tuck Chin to Start", 200, 100);
      } else if (state === 'OVER') {
        ctx.fillText("Game Over", 250, 80);
        ctx.fillText("Score: " + score, 250, 110);
        ctx.fillText("Tuck Chin to Restart", 180, 140);
      } else {
        ctx.fillText("HI " + score, 500, 30);
      }
    }
    
    function update() {
      if(state === 'PLAY') {
        dino.update();
        updateObstacles();
      }
    }
    
    function loop() {
      update();
      draw();
      frames++;
      requestAnimationFrame(loop);
    }
    
    let wasTucked = false;
    
    function onJump() {
      if(state === 'START') {
        state = 'PLAY';
        dino.jumpAction();
      } else if(state === 'PLAY') {
        dino.jumpAction();
      } else if(state === 'OVER') {
        obstacles = [];
        score = 0;
        state = 'START';
      }
    }
    
    window.updatePostureData = function(jsonStr) {
      try {
          let data = JSON.parse(jsonStr);
          let isTucked = data.active_triggers && data.active_triggers['ctar_tuck'] === true;
          
          if(isTucked && !wasTucked) {
              onJump();
          }
          wasTucked = isTucked;
          
          let stat = document.getElementById('status');
          stat.innerText = isTucked ? "TUCKED" : "IDLE";
          stat.style.color = isTucked ? "#0f0" : "red";
      } catch(e) {}
    }
    
    window.addEventListener('keydown', (e) => {
        if(e.code === 'Space') onJump();
    });
    
    window.addEventListener('touchstart', (e) => {
        onJump();
    });
    
    loop();
    </script>
    </body>
    </html>
    """
}
