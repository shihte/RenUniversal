// ─────────────────────────────────────────────────────────────────────────
// EDIT MODAL LOGIC  (技能 / 事件 點擊彈出編輯)
// ─────────────────────────────────────────────────────────────────────────
let _modalContext = { type: null, name: null };

function openEditModal(type, name) {
    _modalContext = { type, name };
    const modal    = document.getElementById('edit-modal');
    const titleEl  = document.getElementById('modal-title');
    const subEl    = document.getElementById('modal-subtitle');
    const syntaxEl = document.getElementById('modal-syntax');

    let currentSyntax = '';
    if (type === 'skill') {
        const skill = (window.loadedSkillsData || []).find(s => s.name === name);
        if (!skill) return;
        titleEl.textContent = `✏️ 編輯技能: ${name.toUpperCase()}`;
        subEl.textContent   = skill.description || '';
        const rules = skill.rules || [];
        if (skill.rule_syntax) {
            currentSyntax = skill.rule_syntax;
        } else if (rules.length > 0) {
            const r0 = rules[0];
            currentSyntax = typeof r0 === 'string' ? r0
                : `${r0.feature||''} ${r0.operator||'>'} ${r0.threshold_key||''}`;
        }
    } else {
        const ev = (window.loadedEventsData || []).find(e => e.name === name);
        if (!ev) return;
        titleEl.textContent = `✏️ 編輯事件: ${name.toUpperCase()}`;
        subEl.textContent   = ev.description || '';
        currentSyntax = Array.isArray(ev.rules) && ev.rules.length > 0
            ? ev.rules.join(' ')
            : (ev.rule_syntax || '');
    }
    syntaxEl.value = currentSyntax;

    const saveBtn = document.getElementById('modal-save-btn');
    let isProgrammatic = false;
    if (type === 'skill') {
        const skill = (window.loadedSkillsData || []).find(s => s.name === name);
        isProgrammatic = skill && (!skill.rules || skill.rules.length === 0) && (!skill.rule_syntax);
    }

    if (isProgrammatic) {
        syntaxEl.readOnly = true;
        syntaxEl.classList.add('opacity-50', 'cursor-not-allowed');
        subEl.innerHTML = `${subEl.textContent} <br><span class="text-red-400 font-bold">⚠️ 此技能由 Python 原生邏輯處理，不支援語法修改。</span>`;
        if (saveBtn) saveBtn.style.display = 'none';
    } else {
        syntaxEl.readOnly = false;
        syntaxEl.classList.remove('opacity-50', 'cursor-not-allowed');
        if (saveBtn) saveBtn.style.display = 'block';
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    syntaxEl.focus();
}

function closeEditModal() {
    const m2 = document.getElementById('edit-modal');
    if(m2) m2.classList.add('hidden');
    const m3 = document.getElementById('edit-modal');
    if(m3) m3.classList.remove('flex');
    _modalContext = { type: null, name: null };
}

// Close on backdrop click
window.addEventListener('DOMContentLoaded', () => {
    const m = document.getElementById('edit-modal');
    if(m) m.addEventListener('click', function(e) {
        if (e.target === this) closeEditModal();
    });
});

async function saveModalEdit() {
    const { type, name } = _modalContext;
    if (!name) return;
    const syntax = document.getElementById('modal-syntax').value.trim();
    if (!syntax) { alert('語法不可為空'); return; }

    let endpoint, bodyData;
    if (type === 'skill') {
        const skill = (window.loadedSkillsData || []).find(s => s.name === name);
        endpoint = '/api/skills/create';
        bodyData = {
            name,
            description: skill?.description || name,
            requirements: skill?.requirements || { face_mesh: true, pose: false },
            rule_syntax: syntax,
            is_update: true
        };
    } else {
        endpoint = '/api/events/create';
        bodyData = { name, rule_syntax: syntax, description: name, enabled: true, is_update: true };
    }

    try {
        const res  = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData)
        });
        const data = await res.json();
        if (data.success || data.status === 'ok') {
            closeEditModal();
            if (type === 'skill') loadSkills();
            else loadEvents();
        } else {
            alert('儲存失敗: ' + (data.error || JSON.stringify(data)));
        }
    } catch(e) {
        alert('連線錯誤: ' + e);
    }
}

// ─────────────────────────────────────────────────────────────────────────
// --- Internationalization ---
const translations = {
    'en': {
        'monitor_dashboard': 'Monitor Dashboard',
        'play_game': 'Play Game',
        'live': 'LIVE',
        'alert_head_down': 'HEAD DOWN',
        'alert_turning': 'TURNING',
        'alert_swaying': 'TORSO SWAYING',
        'alert_leaning': 'LEANING FORWARD',
        'ratio': 'Ratio',
        'sway_ratio': 'Torso Sway',
        'lean_ratio': 'Torso Lean',
        'down_count': 'Down Count',
        'sensitivity_settings': 'Sensitivity Settings',
        'threshold_label': 'Head Down Threshold',
        'threshold_desc': 'Lower value = harder to detect head down',
        'yaw_label': 'Head Turn Tolerance',
        'yaw_desc': 'Higher value = allows more head turning',
        'sway_label': 'Sway Tolerance',
        'sway_desc': 'Adjust tolerance for torso sway.',
        'lean_label': 'Lean Tolerance',
        'lean_desc': 'Adjust tolerance for leaning forward.',
        'actions': 'Actions',
        'detection_active': 'Detection Active',
        'recalibrate': 'Recalibrate Position',
        'recalibrate_hint': 'Look straight ahead and click to reset baseline.',
        'avg_latency': 'Average Latency',
        'camera_source_label': 'Camera Input Source',
        'camera_source_desc': 'Open the Mobile Stream page on your phone, then select Mobile WiFi Stream or Dual-Camera mode.',
        'no_active_events': 'No active events',
        'no_active_skills': 'No active skills',
        'no_active_actions': 'No active actions',
        'triggered': 'TRIGGERED',
        'monitoring': 'MONITORING',
        'active': 'Active',
        'idle': 'Idle',
        'normal': 'Normal',
        'count': 'Count',
        'slouch': 'Slouch',
        'sway': 'Sway',
        'lean': 'Lean'
    },
    'zh-TW': {
        'monitor_dashboard': '監控儀表板',
        'play_game': '開始遊戲',
        'live': '即時影像',
        'alert_head_down': '低頭警示',
        'alert_turning': '轉頭中',
        'alert_swaying': '軀幹搖晃',
        'alert_leaning': '身體前傾',
        'ratio': '比率',
        'sway_ratio': '軀幹搖晃',
        'lean_ratio': '身體前傾',
        'down_count': '低頭次數',
        'sensitivity_settings': '靈敏度設定',
        'threshold_label': '低頭閥值 (Threshold)',
        'threshold_desc': '數值越低，越難觸發低頭判定',
        'yaw_label': '轉頭容忍度 (Tolerance)',
        'yaw_desc': '數值越高，允許頭部轉動幅度越大',
        'sway_label': '左右搖晃容許度 (Sway)',
        'sway_desc': '調整軀幹左右搖晃的敏感門檻',
        'lean_label': '身體前傾容忍度 (Lean)',
        'lean_desc': '調整身體向前傾斜的敏感門檻',
        'actions': '操作面板',
        'detection_active': '啟用姿態偵測',
        'recalibrate': '重新校準基準',
        'recalibrate_hint': '請注視前方並點擊，以重設基準位置。',
        'avg_latency': '平均延遲',
        'camera_source_label': '鏡頭輸入來源 (Camera Source)',
        'camera_source_desc': '在手機上開啟手機串流網頁發送畫面，並在此選擇手機網路串流或雙鏡頭連線模式。',
        'no_active_events': '尚無啟用的事件',
        'no_active_skills': '尚無啟用的技能',
        'no_active_actions': '尚無啟用的動作',
        'triggered': '已觸發 (TRIGGERED)',
        'monitoring': '監控中 (MONITORING)',
        'active': '執行中 (Active)',
        'idle': '待命中 (Idle)',
        'normal': '正常 (Normal)',
        'count': '次數',
        'slouch': '駝背',
        'sway': '搖晃',
        'lean': '前傾'
    }
};

let currentLang = 'zh-TW';

function setLang(lang) {
    currentLang = lang;
    const t = translations[lang];

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) el.textContent = t[key];
    });

    const zhBtn = document.getElementById('btn-zh');
    const enBtn = document.getElementById('btn-en');

    if (lang === 'zh-TW') {
        if(zhBtn) zhBtn.classList.add('bg-gray-700', 'text-white');
        if(enBtn) enBtn.classList.remove('bg-gray-700', 'text-white');
    } else {
        if(enBtn) enBtn.classList.add('bg-gray-700', 'text-white');
        if(zhBtn) zhBtn.classList.remove('bg-gray-700', 'text-white');
    }
}

// ─────────────────────────────────────────────────────────────────────────
// --- Status Update (called by SSE handler) ---
// ─────────────────────────────────────────────────────────────────────────

const statusEl = document.getElementById('connection-status');
const liveIndicator = document.getElementById('live-indicator');
const toggleEl = document.getElementById('detection-toggle');
const privacyCheckbox = document.getElementById('privacy-mode-checkbox');
const flipCheckbox = document.getElementById('flip-enabled-checkbox');

let isUpdatingSettings = false;

function fetchStatus(data) {
    try {
        // Sync toggles with backend state (skip if recently changed by user)
        if (!isUpdatingSettings) {
            if (toggleEl) toggleEl.checked = data.is_active !== false;
            if (privacyCheckbox) privacyCheckbox.checked = data.privacy_mode !== false;
            if (flipCheckbox) flipCheckbox.checked = data.flip_enabled !== false;
        }

        // Update connection status pill
        const pill = document.getElementById('conn-status-pill');
        const dot = document.getElementById('conn-status-dot');
        const statusText = document.getElementById('conn-status-text');
        const fpsEl = document.getElementById('conn-fps-sidebar');

        if (data.connected) {
            if (pill) { pill.className = 'status-pill online'; }
            if (dot) { dot.className = 'status-dot pulsing'; }
            if (statusText) statusText.textContent = 'ONLINE';
        } else {
            if (pill) { pill.className = 'status-pill offline'; }
            if (dot) { dot.className = 'status-dot'; }
            if (statusText) statusText.textContent = 'OFFLINE';
        }
        if (fpsEl) fpsEl.textContent = `${data.fps} FPS`;
        if (liveIndicator) liveIndicator.className = `w-2 h-2 rounded-full ${data.connected ? 'bg-green-400' : 'bg-red-500'} animate-pulse`;

        // Update Stats
        const ratioEl = document.getElementById('ratio-value'); if (ratioEl) ratioEl.textContent = `${data.ratio}%`;
        const latencyEl = document.getElementById('latency-value'); if (latencyEl) latencyEl.textContent = `${data.latency_ms}ms`;
        const fpsDisp = document.getElementById('fps-display'); if (fpsDisp) fpsDisp.textContent = `FPS: ${data.fps}`;

        // Update Active Events Table
        const eventsTbody = document.getElementById('active-events-tbody');
        if (eventsTbody && data.active_events) {
            eventsTbody.innerHTML = '';
            const eventEntries = Object.entries(data.active_events);
            const t = translations[currentLang];

            if (eventEntries.length === 0) {
                eventsTbody.innerHTML = `<tr><td colspan="2" class="py-6 text-center text-slate-400 text-xs">${t['no_active_events']}</td></tr>`;
            } else {
                eventEntries.forEach(([name, isTriggered]) => {
                    const tr = document.createElement('tr');
                    tr.className = 'border-b border-slate-200 transition-colors duration-300';

                    const colorClass = isTriggered ? 'text-red-500 font-medium' : 'text-primary';
                    const statusText = isTriggered ? t['triggered'] : t['monitoring'];
                    const icon = isTriggered ? '🔥' : '👁️';

                    tr.innerHTML = `
                        <td class="py-4 px-2 font-mono ${colorClass}">${icon} ${name}</td>
                        <td class="py-4 px-2 text-right tracking-widest text-[11px] uppercase ${colorClass}">${statusText}</td>
                    `;
                    eventsTbody.appendChild(tr);
                });
            }
        }

        // Update Active Skills Table
        const skillsTbody = document.getElementById('active-skills-tbody');
        if (skillsTbody && data.active_skills) {
            skillsTbody.innerHTML = '';
            const skillEntries = Object.entries(data.active_skills);
            const t = translations[currentLang];

            if (skillEntries.length === 0) {
                skillsTbody.innerHTML = `<tr><td colspan="2" class="py-6 text-center text-slate-500 text-xs">${t['no_active_skills']}</td></tr>`;
            } else {
                skillEntries.forEach(([name, isTriggered]) => {
                    const tr = document.createElement('tr');
                    tr.className = 'border-b border-slate-200 transition-colors duration-300';

                    const colorClass = isTriggered ? 'text-red-500 font-medium' : 'text-primary';
                    const statusText = isTriggered ? t['triggered'] : t['monitoring'];
                    const icon = isTriggered ? '⚠️' : '👁️';

                    tr.innerHTML = `
                        <td class="py-4 px-2 font-mono ${colorClass}">${icon} ${name}</td>
                        <td class="py-4 px-2 text-right tracking-widest text-[11px] uppercase ${colorClass}">${statusText}</td>
                    `;
                    skillsTbody.appendChild(tr);
                });
            }
        }

        // Dynamic Metrics
        const metricsContainer = document.getElementById('dynamic-metrics-container');
        if (metricsContainer && data.metrics) {
            metricsContainer.innerHTML = '';
            const t = translations[currentLang];
            Object.entries(data.metrics).forEach(([name, value]) => {
                const cell = document.createElement('div');
                cell.className = 'metric-cell';
                let label = name.toUpperCase();
                if (name === 'slouch' && t['slouch']) label = t['slouch'];
                if (name === 'sway' && t['sway']) label = t['sway'];
                if (name === 'lean' && t['lean']) label = t['lean'];
                let displayValue = typeof value === 'number' ? `${(value * 100).toFixed(1)}%` : value;
                cell.innerHTML = `
                    <div class="metric-label">${label}</div>
                    <div class="metric-value">${displayValue}</div>
                `;
                metricsContainer.appendChild(cell);
            });
        }

        // Dynamic Trigger Counts
        const countsContainer = document.getElementById('dynamic-counts-container');
        if (countsContainer && data.trigger_counts) {
            countsContainer.innerHTML = '';
            const t = translations[currentLang];
            Object.entries(data.trigger_counts).forEach(([name, count]) => {
                const cell = document.createElement('div');
                cell.className = 'metric-cell';
                let label = `${name.toUpperCase()}`;
                if (name === 'slouch' && t['slouch']) label = t['slouch'];
                if (name === 'sway' && t['sway']) label = t['sway'];
                if (name === 'lean' && t['lean']) label = t['lean'];
                cell.innerHTML = `
                    <div class="metric-label">${label} COUNT</div>
                    <div class="metric-value accent">${count}</div>
                `;
                countsContainer.appendChild(cell);
            });
        }

        const cameraSelect = document.getElementById('camera-source-select');
        if (cameraSelect && !cameraSelect.matches(':focus')) {
            cameraSelect.value = data.camera_source || 'local_0';
        }

        // Sync Tunnel Connection Info
        const tunnelContainer = document.getElementById('tunnel-info-container');
        if (tunnelContainer) {
            const localIp = data.local_ip || '127.0.0.1';
            const localMobileUrl = `https://${localIp}:8443/mobile`;

            const localLinkEl = document.getElementById('local-link');
            const localQrContent = document.getElementById('local-qr-content');
            const localQrWarning = document.getElementById('local-qr-warning');

            if (data.host_bind === '127.0.0.1') {
                if (localQrContent) localQrContent.classList.add('hidden');
                if (localQrWarning) localQrWarning.classList.remove('hidden');
            } else {
                if (localQrContent) localQrContent.classList.remove('hidden');
                if (localQrWarning) localQrWarning.classList.add('hidden');
                if (localLinkEl) {
                    localLinkEl.href = localMobileUrl;
                    localLinkEl.textContent = localMobileUrl;
                    document.getElementById('local-qr').src = `https://quickchart.io/qr?size=150&text=${encodeURIComponent(localMobileUrl)}`;
                }
            }

            const ptb = document.getElementById('public-tunnel-block');
            if(ptb) ptb.classList.remove('hidden');

            const linkEl = document.getElementById('tunnel-link');
            const tunnelQrContent = document.getElementById('tunnel-qr-content');
            const tunnelQrWarning = document.getElementById('tunnel-qr-warning');

            if (data.public_url) {
                if (tunnelQrContent) tunnelQrContent.classList.remove('hidden');
                if (tunnelQrWarning) tunnelQrWarning.classList.add('hidden');
                const mobileUrl = `${data.public_url}/mobile`;
                if (linkEl) {
                    linkEl.href = mobileUrl;
                    linkEl.textContent = mobileUrl;
                    document.getElementById('tunnel-qr').src = `https://quickchart.io/qr?size=150&text=${encodeURIComponent(mobileUrl)}`;
                }
            } else {
                if (tunnelQrContent) tunnelQrContent.classList.add('hidden');
                if (tunnelQrWarning) tunnelQrWarning.classList.remove('hidden');
            }
        }

        // Update active actions/skills badges
        const activeSkillsContainer = document.getElementById('active-skills-badges');
        if (activeSkillsContainer) {
            const t = translations[currentLang];
            if (data.active_skills && Object.keys(data.active_skills).length > 0) {
                activeSkillsContainer.innerHTML = '';
                Object.entries(data.active_skills).forEach(([name, isActive]) => {
                    const badge = document.createElement('span');
                    if (isActive) {
                        badge.className = 'text-xs bg-red-50 text-red-600 px-3 py-1 rounded-full font-medium tracking-tight border border-red-200 animate-pulse';
                        badge.innerText = `${name} ${t['active']}`;
                    } else {
                        badge.className = 'text-xs bg-hairline-soft text-slate-500 px-3 py-1 rounded-full font-medium tracking-tight border border-slate-200';
                        badge.innerText = `${name} ${t['idle']}`;
                    }
                    activeSkillsContainer.appendChild(badge);
                });
            } else {
                activeSkillsContainer.innerHTML = `<span class="text-xs text-slate-500">${t['no_active_actions']}</span>`;
            }
        }

        // Update active events badges
        const activeEventsContainer = document.getElementById('active-events-badges');
        if (activeEventsContainer) {
            const t = translations[currentLang];
            if (data.active_events && Object.keys(data.active_events).length > 0) {
                activeEventsContainer.innerHTML = '';
                Object.entries(data.active_events).forEach(([name, isActive]) => {
                    const badge = document.createElement('span');
                    if (isActive) {
                        badge.className = 'text-xs bg-blue-50 text-primary px-3 py-1 rounded-full font-medium tracking-tight border border-blue-200 animate-pulse';
                        badge.innerText = `${name} ${t['triggered']}`;
                    } else {
                        badge.className = 'text-xs bg-hairline-soft text-slate-500 px-3 py-1 rounded-full font-medium tracking-tight border border-slate-200';
                        badge.innerText = `${name} ${t['normal']}`;
                    }
                    activeEventsContainer.appendChild(badge);
                });
            } else {
                activeEventsContainer.innerHTML = `<span class="text-xs text-slate-500">${t['no_active_events']}</span>`;
            }
        }

    } catch (e) {
        console.error(e);
        if (statusEl) statusEl.className = 'w-3 h-3 rounded-full bg-gray-500';
    }
}

async function updateSetting(key, value) {
    try {
        isUpdatingSettings = true;
        let parsedVal = value;
        if (key !== 'camera_source' && key !== 'flip_enabled' && key !== 'privacy_mode') {
            parsedVal = parseFloat(value);
        }
        await fetch('/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [key]: parsedVal })
        });
    } catch (e) {
        console.error("Failed to update settings", e);
    } finally {
        setTimeout(() => { isUpdatingSettings = false; }, 500);
    }
}

async function toggleDetection(active) {
    try {
        await fetch('/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ active: active })
        });
    } catch (e) { console.error("Failed to toggle detection", e); }
}

async function recalibrate() {
    const icon = document.getElementById('calib-icon');
    const spinner = document.getElementById('calib-spinner');

    icon.classList.add('hidden');
    spinner.classList.remove('hidden');

    try {
        await fetch('/recalibrate', { method: 'POST' });
        setTimeout(() => {
            icon.classList.remove('hidden');
            spinner.classList.add('hidden');
        }, 1000);
    } catch (e) {
        console.error("Failed to recalibrate", e);
        icon.classList.remove('hidden');
        spinner.classList.add('hidden');
    }
}

// --- Skills Tab Actions ---
window.loadedSkillsData = [];
let isUpdateMode = false;

async function loadSkills() {
    try {
        const statusRes = await fetch('/status');
        const statusData = await statusRes.json();

        const res = await fetch('/api/skills');
        const skills = await res.json();
        window.loadedSkillsData = skills;

        const container = document.getElementById('skills-list-container');
        if (!container) return;

        container.innerHTML = '';

        skills.forEach(skill => {
            const card = document.createElement('div');
            card.className = 'anthropic-card p-6 space-y-4';

            const isBuiltin = ['slouch', 'sway', 'lean'].includes(skill.name);
            const isEnabled = skill.enabled !== false;
            const reqs = skill.requirements || {};

            let reqHtml = '';
            if (reqs.face_mesh) reqHtml += '<span class="text-[8px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded font-mono font-bold">FACE MESH</span> ';
            if (reqs.pose)      reqHtml += '<span class="text-[8px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-mono font-bold">POSE</span> ';

            let ruleSyntaxDisplay = '';
            const rules = skill.rules || [];
            if (skill.rule_syntax) {
                ruleSyntaxDisplay = skill.rule_syntax;
            } else if (rules.length > 0) {
                const r0 = rules[0];
                if (typeof r0 === 'string') {
                    ruleSyntaxDisplay = r0;
                } else if (typeof r0 === 'object' && r0 !== null) {
                    const feat  = r0.feature        || '';
                    const op    = r0.operator       || '>';
                    const tkey  = r0.threshold_key  || 'threshold';
                    ruleSyntaxDisplay = `${feat} ${op} ${tkey}`;
                }
            }

            let threshHtml = '';

            let defaultThresh = null;
            if (ruleSyntaxDisplay) {
                const m = ruleSyntaxDisplay.match(/num=(\d+(?:\.\d+)?)(%|px)?/i);
                if (m) defaultThresh = parseFloat(m[1]) / 100.0;
            }

            const defaultPrefs = skill.default_preferences || {};
            if (defaultThresh !== null && Object.keys(defaultPrefs).length === 0) {
                defaultPrefs[`${skill.name}_threshold`] = defaultThresh;
            }

            Object.keys(defaultPrefs).forEach(key => {
                const savedVal = (statusData.prefs && statusData.prefs[key] !== undefined) ? statusData.prefs[key] : defaultPrefs[key];
                const sliderVal = Math.round(savedVal * 100);
                const minRange = (defaultPrefs[key] < 0) ? -100 : 0;

                threshHtml += `
                    <div class="space-y-2 mt-3 pt-3 border-t border-slate-700/30">
                        <div class="flex justify-between items-end">
                            <span class="text-[11px] text-slate-300 font-medium font-sans">${key}</span>
                            <span class="text-xs font-serif italic text-blue-400" id="slider-val-${skill.name}-${key}">${sliderVal}%</span>
                        </div>
                        <input type="range" min="${minRange}" max="100" value="${sliderVal}"
                            oninput="updateSkillPreference('${skill.name}', '${key}', this.value)"
                            onchange="updateSkillPreference('${skill.name}', '${key}', this.value)"
                            class="w-full">
                    </div>
                `;
            });

            card.innerHTML = `
                <div class="flex justify-between items-start">
                    <div class="space-y-1 flex-1 min-w-0 cursor-pointer hover:opacity-80 transition-opacity" onclick="openEditModal('skill','${skill.name}')" title="點擊編輯語法">
                        <div class="flex items-center gap-2 flex-wrap">
                            <h3 class="text-sm font-bold text-white font-heading">${skill.name.toUpperCase()}</h3>
                            ${isBuiltin ? '<span class="text-[8px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded font-bold font-heading">內建核心</span>' : '<span class="text-[8px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded font-bold font-heading">自訂</span>'}
                            <span class="text-[8px] px-1.5 py-0.5 rounded font-mono ${isEnabled ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-500/20 text-slate-400'}">${isEnabled ? '啟用' : '停用'}</span>
                            <span class="text-[8px] text-slate-300 italic">✏️ 點擊編輯</span>
                        </div>
                        <p class="text-xs text-slate-300">${skill.description || ''}</p>
                        <div class="mt-1 flex items-center gap-1.5">${reqHtml}</div>
                        ${ruleSyntaxDisplay ? `<div class="mt-2 bg-slate-800/50 px-2 py-1.5 rounded border border-slate-700/30 font-mono text-[10px] text-emerald-400 truncate" title="${ruleSyntaxDisplay}">語法: ${ruleSyntaxDisplay}</div>` : ''}
                    </div>

                    <div class="flex items-center gap-2 ml-3 flex-shrink-0">
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" class="sr-only peer" ${isEnabled ? 'checked' : ''}
                                onchange="toggleSkill('${skill.name}', this.checked)" onclick="event.stopPropagation()">
                            <div class="w-10 h-5 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                        </label>
                        ${!isBuiltin ? `
                            <button onclick="event.stopPropagation(); deleteSkill('${skill.name}')" class="text-blue-400 hover:text-red-400 text-xs transition-colors p-1" title="刪除">🗑</button>
                        ` : ''}
                    </div>
                </div>
                ${threshHtml}
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Failed to load skills", err);
    }
}

function editSkill(name) {
    const skill = window.loadedSkillsData.find(s => s.name === name);
    if (!skill) return;

    document.getElementById('skill-name').value = skill.name;
    document.getElementById('skill-name').readOnly = true;
    document.getElementById('skill-name').classList.add("opacity-50");
    document.getElementById('skill-desc').value = skill.description || '';
    document.getElementById('req-face').checked = skill.requirements?.face_mesh || false;
    document.getElementById('req-pose').checked = skill.requirements?.pose || false;

    const rules = skill.rules || [];
    if (skill.rule_syntax) {
        document.getElementById('rule-syntax').value = skill.rule_syntax;
    } else if (rules.length > 0) {
        const r0 = rules[0];
        if (typeof r0 === 'string') {
            document.getElementById('rule-syntax').value = r0;
        } else if (typeof r0 === 'object' && r0 !== null) {
            const feat = r0.feature || '';
            const op   = r0.operator || '>';
            const tkey = r0.threshold_key || 'threshold';
            document.getElementById('rule-syntax').value = `${feat} ${op} ${tkey}`;
        }
    } else {
        document.getElementById('rule-syntax').value = '';
    }

    isUpdateMode = true;

    const submitBtn = document.querySelector('#create-skill-form button[type="submit"]');
    submitBtn.innerHTML = '更新並套用動作 (Update Custom Skill)';
    submitBtn.classList.remove('btn-anthropic-primary');
    submitBtn.classList.add('bg-orange-600', 'hover:bg-orange-500', 'text-white');

    if (!document.getElementById('cancel-edit-btn')) {
        const cancelBtn = document.createElement('button');
        cancelBtn.id = 'cancel-edit-btn';
        cancelBtn.type = 'button';
        cancelBtn.className = 'btn-anthropic-secondary w-full py-2 mt-2 text-xs font-bold uppercase tracking-[0.1em] rounded-xl';
        cancelBtn.innerText = '取消編輯 (Cancel)';
        cancelBtn.onclick = resetSkillForm;
        submitBtn.parentNode.insertBefore(cancelBtn, submitBtn.nextSibling);
    }
}

function resetSkillForm() {
    document.getElementById('create-skill-form').reset();
    document.getElementById('skill-name').readOnly = false;
    document.getElementById('skill-name').classList.remove("opacity-50");
    isUpdateMode = false;

    const submitBtn = document.querySelector('#create-skill-form button[type="submit"]');
    submitBtn.innerHTML = '建立並套用動作 (Deploy Custom Skill)';
    submitBtn.classList.add('btn-anthropic-primary');
    submitBtn.classList.remove('bg-orange-600', 'hover:bg-orange-500', 'text-white');

    const cancelBtn = document.getElementById('cancel-edit-btn');
    if (cancelBtn) cancelBtn.remove();
}

async function updateSkillPreference(skillName, key, percentVal) {
    const displayVal = document.getElementById(`slider-val-${skillName}-${key}`);
    if (displayVal) displayVal.textContent = `${percentVal}%`;

    const decimalVal = parseFloat(percentVal) / 100.0;
    try {
        await fetch('/api/settings/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [key]: decimalVal })
        });
    } catch (e) {
        console.error("Failed to update skill preference", e);
    }
}

async function toggleSkill(name, enabled) {
    try {
        const res = await fetch('/api/skills/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, enabled })
        });
        const data = await res.json();
        if (data.success) {
            loadSkills();
        } else {
            alert("Error: " + data.error);
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteSkill(name) {
    if (!confirm(`確定要刪除自訂動作包 "${name}" 嗎？`)) return;
    try {
        const res = await fetch('/api/skills/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success) {
            loadSkills();
        } else {
            alert("Error: " + data.error);
        }
    } catch (err) {
        console.error(err);
    }
}

async function submitCreateSkill(e) {
    e.preventDefault();
    const name = document.getElementById('skill-name').value.trim();
    const desc = document.getElementById('skill-desc').value.trim();
    const faceMesh = document.getElementById('req-face').checked;
    const pose = document.getElementById('req-pose').checked;

    const syntaxStr = document.getElementById('rule-syntax').value.trim();

    if (!name) {
        alert("請填寫動作包名稱");
        return;
    }
    if (!syntaxStr) {
        alert("請填寫動作成立語法");
        return;
    }
    if (!faceMesh && !pose) {
        alert("請至少選擇一種演算法依賴 (Face Mesh 或 Pose)");
        return;
    }

    const bodyData = {
        name,
        description: desc,
        requirements: {
            face_mesh: faceMesh,
            pose: pose
        },
        rule_syntax: syntaxStr,
        default_preferences: {},
        is_update: isUpdateMode
    };

    try {
        const res = await fetch('/api/skills/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData)
        });
        const data = await res.json();
        if (data.success) {
            alert(isUpdateMode ? "動作包更新成功！" : "動作包載入成功！已套用至判定引擎。");
            resetSkillForm();
            loadSkills();
        } else {
            alert("操作失敗: " + data.error);
        }
    } catch (err) {
        alert("連線錯誤: " + err);
    }
}

// --- Events Tab Actions ---
window.loadedEventsData = [];
let isEventUpdateMode = false;

async function loadEvents() {
    try {
        const res = await fetch('/api/events');
        const events = await res.json();
        window.loadedEventsData = events;

        const container = document.getElementById('events-list-container');
        if (!container) return;

        container.innerHTML = '';

        if (events.length === 0) {
            container.innerHTML = `
                <div class="anthropic-card p-8 text-center text-xs text-slate-300 italic">
                    尚未建立任何複合事件規則。請在右側表單建立第一個規則。
                </div>
            `;
            return;
        }

        events.forEach(event => {
            const card = document.createElement('div');
            card.className = 'anthropic-card p-6 space-y-4';

            const isEnabled = event.enabled !== false;

            card.innerHTML = `
                <div class="flex justify-between items-start">
                    <div class="space-y-1 flex-1 cursor-pointer hover:opacity-80 transition-opacity" onclick="openEditModal('event','${event.name}')" title="點擊編輯語法">
                        <div class="flex items-center gap-2">
                            <h3 class="text-sm font-bold text-white font-heading">${event.name.toUpperCase()}</h3>
                            <span class="text-[8px] text-slate-300 italic">✏️ 點擊編輯</span>
                        </div>
                        <p class="text-xs text-slate-300">${event.description || ''}</p>
                        <div class="mt-2 bg-slate-800/50 p-2 rounded border border-slate-700/30 font-mono text-[10px] text-white">
                            語法: <span class="text-blue-400">${(event.rules && Array.isArray(event.rules)) ? event.rules.join(' ') : (event.rule_syntax || '')}</span>
                        </div>
                    </div>

                    <div class="flex items-center gap-3 ml-3 flex-shrink-0">
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" class="sr-only peer" ${isEnabled ? 'checked' : ''}
                                onchange="toggleEvent('${event.name}', this.checked)" onclick="event.stopPropagation()">
                            <div class="w-10 h-5 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                        </label>
                        <button onclick="event.stopPropagation(); deleteEvent('${event.name}')" class="text-blue-400 hover:text-red-400 text-xs transition-colors p-1">🗑</button>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Failed to load events", err);
    }
}

function editEvent(name) {
    const event = window.loadedEventsData.find(e => e.name === name);
    if (!event) return;

    document.getElementById('event-name').value = event.name;
    document.getElementById('event-name').readOnly = true;
    document.getElementById('event-name').classList.add("opacity-50");
    document.getElementById('event-desc').value = event.description || '';
    document.getElementById('event-syntax').value = (event.rules && Array.isArray(event.rules)) ? event.rules.join(' ') : (event.rule_syntax || '');

    isEventUpdateMode = true;

    const submitBtn = document.querySelector('#create-event-form button[type="submit"]');
    submitBtn.innerHTML = '更新並套用事件 (Update Event)';
    submitBtn.classList.remove('btn-anthropic-primary');
    submitBtn.classList.add('bg-orange-600', 'hover:bg-orange-500', 'text-white');

    if (!document.getElementById('cancel-event-edit-btn')) {
        const cancelBtn = document.createElement('button');
        cancelBtn.id = 'cancel-event-edit-btn';
        cancelBtn.type = 'button';
        cancelBtn.className = 'btn-anthropic-secondary w-full py-2 mt-2 text-xs font-bold uppercase tracking-[0.1em] rounded-xl';
        cancelBtn.innerText = '取消編輯 (Cancel)';
        cancelBtn.onclick = resetEventForm;
        submitBtn.parentNode.insertBefore(cancelBtn, submitBtn.nextSibling);
    }
}

function resetEventForm() {
    document.getElementById('create-event-form').reset();
    document.getElementById('event-name').readOnly = false;
    document.getElementById('event-name').classList.remove("opacity-50");
    isEventUpdateMode = false;

    const submitBtn = document.querySelector('#create-event-form button[type="submit"]');
    submitBtn.innerHTML = '建立並套用事件 (Deploy Event)';
    submitBtn.classList.add('btn-anthropic-primary');
    submitBtn.classList.remove('bg-orange-600', 'hover:bg-orange-500', 'text-white');

    const cancelBtn = document.getElementById('cancel-event-edit-btn');
    if (cancelBtn) cancelBtn.remove();
}

async function toggleEvent(name, enabled) {
    try {
        const res = await fetch('/api/events/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, enabled })
        });
        const data = await res.json();
        if (data.success) {
            loadEvents();
        } else {
            alert("Error: " + data.error);
        }
    } catch (err) {
        console.error(err);
    }
}

async function deleteEvent(name) {
    if (!confirm(`確定要刪除自訂複合事件 "${name}" 嗎？`)) return;
    try {
        const res = await fetch('/api/events/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (data.success) {
            loadEvents();
        } else {
            alert("Error: " + data.error);
        }
    } catch (err) {
        console.error(err);
    }
}

async function submitCreateEvent(e) {
    e.preventDefault();
    const name = document.getElementById('event-name').value.trim();
    const desc = document.getElementById('event-desc').value.trim();
    const syntaxStr = document.getElementById('event-syntax').value.trim();

    if (!name) {
        alert("請填寫事件名稱");
        return;
    }
    if (!syntaxStr) {
        alert("請填寫事件成立邏輯語法");
        return;
    }

    const bodyData = {
        name,
        description: desc,
        rules: [syntaxStr],
        is_update: isEventUpdateMode
    };

    try {
        const res = await fetch('/api/events/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData)
        });
        const data = await res.json();
        if (data.success) {
            alert(isEventUpdateMode ? "複合事件更新成功！" : "複合事件載入成功！已套用至判定引擎。");
            resetEventForm();
            loadEvents();
        } else {
            alert("操作失敗: " + data.error);
        }
    } catch (err) {
        alert("連線錯誤: " + err);
    }
}

async function loadAvailableCameras() {
    try {
        const res = await fetch('/cameras');
        const cameras = await res.json();
        const select = document.getElementById('camera-source-select');
        if (!select) return;

        const currentValue = select.value;

        const nonLocalOptions = [];
        for (let option of select.options) {
            if (!option.value.startsWith('local_')) {
                nonLocalOptions.push({ value: option.value, text: option.innerText });
            }
        }

        select.innerHTML = '';

        cameras.forEach(index => {
            const opt = document.createElement('option');
            opt.value = `local_${index}`;
            if (index === 0) {
                opt.text = '電腦預設鏡頭 (Local Camera 0)';
            } else {
                opt.text = `USB外接鏡頭 ${index} (Local Camera ${index})`;
            }
            select.appendChild(opt);
        });

        nonLocalOptions.forEach(optData => {
            const opt = document.createElement('option');
            opt.value = optData.value;
            opt.text = optData.text;
            select.appendChild(opt);
        });

        if (currentValue) {
            select.value = currentValue;
        }
    } catch (err) {
        console.error("Failed to load local cameras", err);
    }
}

// ─────────────────────────────────────────────────────────────────────────
// --- SSE Status Stream (replaces 100ms polling) ---
// ─────────────────────────────────────────────────────────────────────────
function initSSE() {
    const es = new EventSource('/api/status/stream');
    es.onmessage = (event) => {
        try {
            fetchStatus(JSON.parse(event.data));
        } catch (e) {
            console.error('SSE parse error', e);
        }
    };
    es.onerror = () => {
        // Browser auto-reconnects; close and reopen after a short delay to avoid rapid loops
        es.close();
        setTimeout(initSSE, 3000);
    };
}

// Initialize
setLang('zh-TW');
loadAvailableCameras();
initSSE();
