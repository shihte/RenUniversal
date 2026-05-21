import re

with open('web/game.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_logic = """
        const PostureController = {
            apiUrl: '/status',  // Use relative path for single server architecture
            pollInterval: 100,  // 100ms polling
            isConnected: false,
            wasHeadDown: false,  // 用於偵測狀態變化（邊緣觸發）
            lastDownCount: 0,    // 追蹤低頭次數變化
            intervalId: null,

            init() {
                this.startPolling();
                this.updateUI(false, 'Connecting...');
            },

            startPolling() {
                if (this.intervalId) clearInterval(this.intervalId);
                this.intervalId = setInterval(() => this.poll(), this.pollInterval);
            },

            async poll() {
                try {
                    const res = await fetch(this.apiUrl, {
                        signal: AbortSignal.timeout(500)
                    });

                    if (!res.ok) throw new Error('Not OK');

                    const data = await res.json();

                    if (!this.isConnected) {
                        this.isConnected = true;
                        this.lastDownCount = data.down_count;
                    }

                    // 校準中
                    if (data.calibrating) {
                        this.updateUI(true, `Calibrating ${data.calibration_progress}%`);
                        return;
                    }

                    // 轉頭中
                    if (data.is_turning) {
                        this.updateUI(true, 'Turning...');
                        return;
                    }

                    let statusText = `Ratio: ${data.ratio}%`;
                    if (data.is_bad_posture) {
                        statusText = '👇 HEAD DOWN';
                    }
                    
                    let extraAlerts = [];
                    if (data.is_swaying) {
                        extraAlerts.push('↔️ SWAYING');
                    }
                    if (data.is_leaning_forward) {
                        extraAlerts.push('🔍 LEANING');
                    }
                    
                    if (extraAlerts.length > 0) {
                        statusText = `${statusText} (${extraAlerts.join(' + ')})`;
                    }

                    // 偵測低頭次數變化（邊緣觸發）
                    if (data.down_count > this.lastDownCount) {
                        // 低頭次數增加 = 觸發跳躍
                        this.triggerJump();
                        this.lastDownCount = data.down_count;
                        this.updateUI(true, `👇 HEAD DOWN! | ${data.latency_ms}ms`);
                    } else {
                        // Show ratio, extra alerts, and latency
                        this.updateUI(true, `${statusText} | ${data.latency_ms}ms`);
                    }

                } catch (error) {
                    this.isConnected = false;
                    this.updateUI(false, 'Disconnected');
                }
            },
"""

new_logic = """
        const PostureController = {
            apiUrl: '/status',
            pollInterval: 100,
            isConnected: false,
            lastTriggerCount: 0,
            intervalId: null,

            init() {
                this.startPolling();
                this.updateUI(false, 'Connecting...');
            },

            startPolling() {
                if (this.intervalId) clearInterval(this.intervalId);
                this.intervalId = setInterval(() => this.poll(), this.pollInterval);
            },

            async poll() {
                try {
                    const res = await fetch(this.apiUrl, {
                        signal: AbortSignal.timeout(500)
                    });

                    if (!res.ok) throw new Error('Not OK');

                    const data = await res.json();
                    
                    let currentTriggerCount = 0;
                    if (data.trigger_counts) {
                        currentTriggerCount = Object.values(data.trigger_counts).reduce((a, b) => a + b, 0);
                    } else if (data.down_count !== undefined) {
                        currentTriggerCount = data.down_count;
                    }

                    if (!this.isConnected) {
                        this.isConnected = true;
                        this.lastTriggerCount = currentTriggerCount;
                    }

                    if (data.calibrating) {
                        this.updateUI(true, `Calibrating ${data.calibration_progress}%`);
                        return;
                    }

                    let activeNames = [];
                    if (data.active_events) {
                        Object.entries(data.active_events).forEach(([name, active]) => {
                            if (active) activeNames.push(name.toUpperCase());
                        });
                    }
                    if (data.active_skills) {
                        Object.entries(data.active_skills).forEach(([name, active]) => {
                            if (active && !activeNames.includes(name.toUpperCase())) {
                                activeNames.push(name.toUpperCase());
                            }
                        });
                    }
                    
                    let statusText = activeNames.length > 0 ? activeNames.join(' + ') : 'IDLE';

                    if (currentTriggerCount > this.lastTriggerCount) {
                        this.triggerJump();
                        this.lastTriggerCount = currentTriggerCount;
                        this.updateUI(true, `⚡ ACTION! (${statusText}) | ${data.latency_ms}ms`);
                    } else {
                        this.updateUI(true, `${statusText} | ${data.latency_ms}ms`);
                    }

                } catch (error) {
                    this.isConnected = false;
                    this.updateUI(false, 'Disconnected');
                }
            },
"""

if old_logic.strip() in content:
    content = content.replace(old_logic.strip(), new_logic.strip())
    print("Replaced successfully")
else:
    print("Could not find old_logic in game.html")

with open('web/game.html', 'w', encoding='utf-8') as f:
    f.write(content)

