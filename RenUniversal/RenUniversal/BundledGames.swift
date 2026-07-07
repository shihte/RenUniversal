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
    static let statisticsHtml = #"""
<!DOCTYPE html>
<html lang="zh-TW" class="dark">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>姿勢統計工具 (Statistics Tool)</title>
    <script src="/tailwind.js"></script>
    <style>
        body {
            background-color: #0f172a;
            color: #f8fafc;
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
        }

        /* Custom Scrollbar for the table */
        .custom-scrollbar::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.3);
        }
    </style>
</head>

<body class="min-h-screen flex flex-col items-center py-8 px-4 sm:px-8">
    <div class="w-full max-w-6xl flex justify-between items-end mb-8">
        <div>
            <h1 class="text-3xl font-bold tracking-wider text-white flex items-center gap-3">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                姿勢統計分析
            </h1>
            <p class="text-sm text-slate-400 mt-2">自動追蹤、計算與分類姿勢事件，重整頁面將清除資料</p>
        </div>

        <div id="connection-status" class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700">
            <div id="status-dot" class="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></div>
            <span id="status-text" class="text-xs font-medium text-slate-300">連線中...</span>
        </div>
    </div>

    <!-- 儀表板卡片區 -->
    <div class="w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <!-- 總計次數 -->
        <div class="bg-slate-800/80 backdrop-blur border border-slate-700 rounded-xl p-5 flex flex-col justify-between shadow-lg">
            <div class="text-slate-400 text-sm font-medium tracking-wide">總觸發次數</div>
            <div class="text-4xl font-bold text-white mt-2" id="stat-total">0</div>
            <div class="mt-4 text-xs text-slate-500">所有類型的事件總和</div>
        </div>

        <!-- 有效次數 -->
        <div class="bg-blue-900/20 backdrop-blur border border-blue-800/50 rounded-xl p-5 flex flex-col justify-between shadow-lg">
            <div class="flex justify-between items-center">
                <div class="text-blue-300 text-sm font-medium tracking-wide">有效姿勢不良</div>
                <div class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400">>= <span id="lbl-valid-threshold">1.5</span>s</div>
            </div>
            <div class="text-4xl font-bold text-blue-400 mt-2" id="stat-valid">0</div>
            <div class="mt-4 text-xs text-slate-500 flex justify-between items-center">
                <span>持續時間超過閾值</span>
                <input type="range" id="valid-threshold-slider" min="0.5" max="5.0" step="0.5" value="1.5" class="w-24 accent-blue-500 cursor-pointer">
            </div>
        </div>

        <!-- 無效次數 (雜訊) -->
        <div class="bg-slate-800/80 backdrop-blur border border-slate-700 rounded-xl p-5 flex flex-col justify-between shadow-lg">
            <div class="text-slate-400 text-sm font-medium tracking-wide">無效次數 (雜訊)</div>
            <div class="text-4xl font-bold text-slate-300 mt-2" id="stat-invalid">0</div>
            <div class="mt-4 text-xs text-slate-500">短暫動作，低於閾值</div>
        </div>

        <!-- 總時長 -->
        <div class="bg-slate-800/80 backdrop-blur border border-slate-700 rounded-xl p-5 flex flex-col justify-between shadow-lg">
            <div class="text-slate-400 text-sm font-medium tracking-wide">累積不良時長</div>
            <div class="text-4xl font-bold text-white mt-2" id="stat-duration">0.0<span class="text-lg text-slate-500 ml-1">s</span></div>
            <div class="mt-4 text-xs text-slate-500">有效事件的總持續時間</div>
        </div>
    </div>

    <!-- 錯誤類型分類與即時狀態 -->
    <div class="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        
        <!-- 左側：類型分佈圖表 (單純用 Progress bars 實作) -->
        <div class="lg:col-span-1 bg-slate-800/80 backdrop-blur border border-slate-700 rounded-xl p-6 shadow-lg">
            <h2 class="text-lg font-semibold text-white mb-6">錯誤類型分佈</h2>
            <div class="flex flex-col gap-5">
                <!-- Tilt -->
                <div>
                    <div class="flex justify-between text-sm mb-1">
                        <span class="text-slate-300">歪頭 (Tilt)</span>
                        <span class="text-white font-mono" id="count-tilt">0</span>
                    </div>
                    <div class="w-full bg-slate-700 rounded-full h-2">
                        <div class="bg-purple-500 h-2 rounded-full transition-all duration-500" style="width: 0%" id="bar-tilt"></div>
                    </div>
                </div>
                <!-- Turn -->
                <div>
                    <div class="flex justify-between text-sm mb-1">
                        <span class="text-slate-300">轉頭 (Turn)</span>
                        <span class="text-white font-mono" id="count-turn">0</span>
                    </div>
                    <div class="w-full bg-slate-700 rounded-full h-2">
                        <div class="bg-indigo-500 h-2 rounded-full transition-all duration-500" style="width: 0%" id="bar-turn"></div>
                    </div>
                </div>
                <!-- Slouch -->
                <div>
                    <div class="flex justify-between text-sm mb-1">
                        <span class="text-slate-300">駝背 (Slouch)</span>
                        <span class="text-white font-mono" id="count-slouch">0</span>
                    </div>
                    <div class="w-full bg-slate-700 rounded-full h-2">
                        <div class="bg-amber-500 h-2 rounded-full transition-all duration-500" style="width: 0%" id="bar-slouch"></div>
                    </div>
                </div>
                <!-- Lean -->
                <div>
                    <div class="flex justify-between text-sm mb-1">
                        <span class="text-slate-300">前傾 (Lean)</span>
                        <span class="text-white font-mono" id="count-lean">0</span>
                    </div>
                    <div class="w-full bg-slate-700 rounded-full h-2">
                        <div class="bg-rose-500 h-2 rounded-full transition-all duration-500" style="width: 0%" id="bar-lean"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 右側：即時日誌清單 -->
        <div class="lg:col-span-2 bg-slate-800/80 backdrop-blur border border-slate-700 rounded-xl p-0 shadow-lg flex flex-col overflow-hidden h-[400px]">
            <div class="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800/90">
                <h2 class="text-lg font-semibold text-white">即時事件紀錄</h2>
                <div class="flex gap-2">
                    <button id="btn-clear" class="px-3 py-1.5 text-xs font-medium bg-slate-700 hover:bg-slate-600 text-white rounded transition-colors">清除紀錄</button>
                    <button id="btn-export" class="px-3 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded shadow transition-colors flex items-center gap-1">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        匯出 CSV
                    </button>
                </div>
            </div>
            
            <div class="flex-1 overflow-auto custom-scrollbar bg-slate-900/50 relative">
                <table class="w-full text-left text-sm text-slate-400">
                    <thead class="text-xs uppercase bg-slate-800/80 text-slate-300 sticky top-0 backdrop-blur">
                        <tr>
                            <th scope="col" class="px-6 py-3 font-medium tracking-wider">觸發時間</th>
                            <th scope="col" class="px-6 py-3 font-medium tracking-wider">錯誤類型</th>
                            <th scope="col" class="px-6 py-3 font-medium tracking-wider">持續時間</th>
                            <th scope="col" class="px-6 py-3 font-medium tracking-wider text-center">判定</th>
                        </tr>
                    </thead>
                    <tbody id="log-table-body" class="divide-y divide-slate-800/50">
                        <!-- Logs will be inserted here -->
                        <tr id="empty-row">
                            <td colspan="4" class="px-6 py-12 text-center text-slate-500">
                                尚無任何姿勢紀錄
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- 即時狀態小圖示群 -->
    <div class="fixed bottom-4 right-4 flex gap-2" id="live-badges">
        <!-- JS 將會即時切換這些 badge 的透明度 -->
        <div id="badge-tilt" class="px-2 py-1 rounded text-[10px] font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30 opacity-30 transition-opacity">TILT</div>
        <div id="badge-turn" class="px-2 py-1 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 opacity-30 transition-opacity">TURN</div>
        <div id="badge-slouch" class="px-2 py-1 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 opacity-30 transition-opacity">SLOUCH</div>
        <div id="badge-lean" class="px-2 py-1 rounded text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 opacity-30 transition-opacity">LEAN</div>
    </div>

    <script>
        // 目標追蹤的類型
        const TRACKED_SKILLS = ['tilt', 'turn', 'slouch', 'lean'];
        
        // 狀態管理
        let state = {
            logs: [],
            stats: {
                total: 0,
                valid: 0,
                invalid: 0,
                totalDurationMs: 0,
                types: {
                    tilt: 0,
                    turn: 0,
                    slouch: 0,
                    lean: 0
                }
            },
            activeEvents: {}, // skill_name -> { startTime }
            validThresholdMs: 1500 // 1.5s 預設
        };

        // DOM 元素
        const els = {
            statusDot: document.getElementById('status-dot'),
            statusText: document.getElementById('status-text'),
            statTotal: document.getElementById('stat-total'),
            statValid: document.getElementById('stat-valid'),
            statInvalid: document.getElementById('stat-invalid'),
            statDuration: document.getElementById('stat-duration'),
            logTableBody: document.getElementById('log-table-body'),
            emptyRow: document.getElementById('empty-row'),
            slider: document.getElementById('valid-threshold-slider'),
            lblThreshold: document.getElementById('lbl-valid-threshold'),
            btnClear: document.getElementById('btn-clear'),
            btnExport: document.getElementById('btn-export'),
        };

        // 更新閾值 UI
        els.slider.addEventListener('input', (e) => {
            els.lblThreshold.textContent = parseFloat(e.target.value).toFixed(1);
            state.validThresholdMs = parseFloat(e.target.value) * 1000;
            // 重新計算歷史 log 的 valid/invalid 狀態
            recalculateValidity();
        });

        // 重新計算有效性
        function recalculateValidity() {
            state.stats.valid = 0;
            state.stats.invalid = 0;
            state.stats.totalDurationMs = 0;
            
            state.logs.forEach(log => {
                log.isValid = log.durationMs >= state.validThresholdMs;
                if (log.isValid) {
                    state.stats.valid++;
                    state.stats.totalDurationMs += log.durationMs;
                } else {
                    state.stats.invalid++;
                }
            });
            updateDashboardUI();
            renderTable();
        }

        // 格式化時間戳
        function formatTime(date) {
            return date.toTimeString().split(' ')[0] + '.' + String(date.getMilliseconds()).padStart(3, '0').slice(0, 2);
        }

        // 當事件結束時新增 Log
        function addLog(type, startTime, endTime) {
            const durationMs = endTime - startTime;
            const isValid = durationMs >= state.validThresholdMs;

            const log = {
                id: Date.now().toString() + Math.random().toString(36).substr(2, 5),
                type: type,
                startTime: startTime,
                endTime: endTime,
                durationMs: durationMs,
                isValid: isValid
            };

            state.logs.unshift(log); // 最新放前面
            
            // 更新統計
            state.stats.total++;
            state.stats.types[type] = (state.stats.types[type] || 0) + 1;
            if (isValid) {
                state.stats.valid++;
                state.stats.totalDurationMs += durationMs;
            } else {
                state.stats.invalid++;
            }

            updateDashboardUI();
            renderTable();
        }

        // 渲染統計數據
        function updateDashboardUI() {
            els.statTotal.textContent = state.stats.total;
            els.statValid.textContent = state.stats.valid;
            els.statInvalid.textContent = state.stats.invalid;
            els.statDuration.innerHTML = (state.stats.totalDurationMs / 1000).toFixed(1) + '<span class="text-lg text-slate-500 ml-1">s</span>';

            // 更新長條圖與數字
            const maxCount = Math.max(...Object.values(state.stats.types), 1);
            TRACKED_SKILLS.forEach(skill => {
                const count = state.stats.types[skill] || 0;
                const pct = (count / maxCount) * 100;
                const countEl = document.getElementById(`count-${skill}`);
                const barEl = document.getElementById(`bar-${skill}`);
                if (countEl) countEl.textContent = count;
                if (barEl) barEl.style.width = `${pct}%`;
            });
        }

        // 渲染表格
        function renderTable() {
            if (state.logs.length === 0) {
                els.logTableBody.innerHTML = `
                    <tr id="empty-row">
                        <td colspan="4" class="px-6 py-12 text-center text-slate-500">尚無任何姿勢紀錄</td>
                    </tr>`;
                return;
            }

            let html = '';
            // 最多顯示最新的 100 筆，避免 DOM 過於肥大 (但匯出時匯出全部)
            const displayLogs = state.logs.slice(0, 100);
            
            const typeLabels = {
                tilt: '<span class="text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded font-medium">歪頭 (Tilt)</span>',
                turn: '<span class="text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded font-medium">轉頭 (Turn)</span>',
                slouch: '<span class="text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded font-medium">駝背 (Slouch)</span>',
                lean: '<span class="text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded font-medium">前傾 (Lean)</span>'
            };

            displayLogs.forEach(log => {
                const label = typeLabels[log.type] || log.type;
                const timeStr = formatTime(new Date(log.startTime));
                const durStr = (log.durationMs / 1000).toFixed(2) + 's';
                
                const validHtml = log.isValid 
                    ? `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/20 text-blue-400 border border-blue-500/20">有效</span>`
                    : `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-300">無效 (雜訊)</span>`;

                html += `
                    <tr class="hover:bg-slate-700/30 transition-colors">
                        <td class="px-6 py-3 whitespace-nowrap font-mono text-slate-300">${timeStr}</td>
                        <td class="px-6 py-3 whitespace-nowrap">${label}</td>
                        <td class="px-6 py-3 whitespace-nowrap font-mono text-slate-300">${durStr}</td>
                        <td class="px-6 py-3 whitespace-nowrap text-center">${validHtml}</td>
                    </tr>
                `;
            });
            els.logTableBody.innerHTML = html;
        }

        // 清除紀錄
        els.btnClear.addEventListener('click', () => {
            if (confirm("確定要清除所有目前紀錄嗎？（匯出資料也會清空）")) {
                state.logs = [];
                state.stats.total = 0;
                state.stats.valid = 0;
                state.stats.invalid = 0;
                state.stats.totalDurationMs = 0;
                TRACKED_SKILLS.forEach(s => state.stats.types[s] = 0);
                updateDashboardUI();
                renderTable();
            }
        });

        // 匯出 CSV
        els.btnExport.addEventListener('click', () => {
            if (state.logs.length === 0) {
                alert("目前沒有紀錄可匯出！");
                return;
            }

            let csvContent = "data:text/csv;charset=utf-8,\uFEFF";
            csvContent += "Event ID,Start Time,End Time,Type,Duration (s),Is Valid\r\n";

            state.logs.forEach(log => {
                const st = new Date(log.startTime).toISOString();
                const et = new Date(log.endTime).toISOString();
                const dur = (log.durationMs / 1000).toFixed(3);
                const validStr = log.isValid ? "Yes" : "No";
                csvContent += `${log.id},${st},${et},${log.type},${dur},${validStr}\r\n`;
            });

            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `posture_statistics_${new Date().toISOString().split('T')[0]}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });

        // 定期輪詢 API (與 Game.html 類似，這裡為了輕量化選用 fetch)
        async function pollStatus() {
            try {
                const res = await fetch('/status', { signal: AbortSignal.timeout(1000) });
                if (!res.ok) throw new Error('Network error');
                const data = await res.json();
                
                // 更新連線狀態 UI
                els.statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse";
                els.statusText.textContent = `已連線 (${data.latency_ms}ms)`;

                const now = Date.now();
                const currentSkills = data.active_skills || {};

                TRACKED_SKILLS.forEach(skill => {
                    const isActiveNow = !!currentSkills[skill];
                    const wasActive = !!state.activeEvents[skill];

                    // 即時狀態 Badge 更新
                    const badge = document.getElementById(`badge-${skill}`);
                    if (badge) {
                        badge.style.opacity = isActiveNow ? '1' : '0.3';
                        badge.style.transform = isActiveNow ? 'scale(1.1)' : 'scale(1)';
                    }

                    if (isActiveNow && !wasActive) {
                        // 狀態改變: False -> True (開始)
                        state.activeEvents[skill] = { startTime: now };
                    } else if (!isActiveNow && wasActive) {
                        // 狀態改變: True -> False (結束)
                        const eventData = state.activeEvents[skill];
                        addLog(skill, eventData.startTime, now);
                        delete state.activeEvents[skill];
                    }
                });

            } catch (err) {
                // 連線失敗
                els.statusDot.className = "w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse";
                els.statusText.textContent = "連線中斷或重試中...";
            }
        }

        // 啟動輪詢
        setInterval(pollStatus, 100);

        // 初始渲染
        updateDashboardUI();
        renderTable();
    </script>
</body>

</html>

"""#
}
