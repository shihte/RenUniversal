import re

with open('web/Monitor.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Restore the lost documentation in the Skills Tab
skills_doc = """                                                <li><code class="text-[#d97757]">p11</code>: 左肩 (Left Shoulder)</li>
                                                <li><code class="text-[#d97757]">p12</code>: 右肩 (Right Shoulder)</li>
                                                <li><code class="text-[#d97757]">p13</code>: 左肘 (Left Elbow)</li>
                                                <li><code class="text-[#d97757]">p14</code>: 右肘 (Right Elbow)</li>
                                                <li><code class="text-[#d97757]">p15</code>: 左手腕 (Left Wrist)</li>
                                                <li><code class="text-[#d97757]">p16</code>: 右手腕 (Right Wrist)</li>
                                                <li><code class="text-[#d97757]">p0</code>: 鼻尖 (Nose)</li>
                                            </ul>
                                        </div>
                                        <div>
                                            <span class="font-bold text-[#788c5d] block mb-1">👤 面部網格點位 (Face Mesh)</span>
                                            <ul class="space-y-0.5 list-disc list-inside">
                                                <li><code class="text-[#d97757]">f33</code>: 左眼外角</li>
                                                <li><code class="text-[#d97757]">f263</code>: 右眼外角</li>
                                                <li><code class="text-[#d97757]">f1</code>: 鼻尖</li>
                                                <li><code class="text-[#d97757]">f152</code>: 下巴底端</li>
                                                <li><code class="text-[#d97757]">f13</code>: 上唇內側</li>
                                                <li><code class="text-[#d97757]">f14</code>: 下唇內側</li>
                                                <li><code class="text-[#d97757]">f4</code>: 鼻梁</li>
                                            </ul>
                                        </div>
                                    </div>
                                    <div class="text-[9px] text-[#706e68] border-t border-[#b0aea5]/5 pt-1">
                                        💡 提示：點位前綴 <code class="text-white">p</code> 代表身體 (0-32)，<code class="text-white">f</code> 代表臉部 (0-467)。可以直接輸入數字。
                                    </div>"""

bad_chunk = """                                                <li><code class="text-[#d97757]">p11</code>: 左肩 (Left Shoulder)</li>
                                                <li><code class="text-[#d97757]">p12</code>: 右肩 (Right Shoulder)</li>
                                    </div>"""

if bad_chunk in content:
    content = content.replace(bad_chunk, skills_doc)
    print("Fixed Skills tab documentation")

# 2. Restore the Point ID helper in the Events tab (generator-pt1)
events_generator = """                            <!-- Point ID Generator -->
                            <div class="bg-[#151513] p-4 rounded-xl border border-[#b0aea5]/10 space-y-3 mb-4">
                                <label class="text-[10px] text-[#b0aea5] block font-semibold">🔗 點位規則產生器 (Point Rule Generator)</label>
                                <div class="grid grid-cols-2 gap-3">
                                    <div>
                                        <label class="text-[9px] text-[#706e68] block">點位 1 ID</label>
                                        <input type="text" id="generator-pt1" placeholder="例: f1" class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757] font-mono">
                                    </div>
                                    <div>
                                        <label class="text-[9px] text-[#706e68] block">點位 2 ID</label>
                                        <input type="text" id="generator-pt2" placeholder="例: f152" class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757] font-mono">
                                    </div>
                                </div>
                                <div class="grid grid-cols-2 gap-3">
                                    <div>
                                        <label class="text-[9px] text-[#706e68] block">變化方向</label>
                                        <select id="generator-op" class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757]">
                                            <option value="><">>< 縮短 (Shrink)</option>
                                            <option value="<>"><> 放大 (Expand)</option>
                                            <option value=">><<">>><< 變化 (Both)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label class="text-[9px] text-[#706e68] block">臨界比例 (%)</label>
                                        <input type="number" id="generator-num" value="20" min="1" max="100" class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757] font-mono">
                                    </div>
                                </div>
                                <div class="flex gap-2">
                                    <button type="button" onclick="insertPointRule('AND')" class="flex-1 bg-[#2a2a28] hover:bg-[#3a3a38] text-[#b0aea5] text-[10px] py-1.5 rounded font-semibold transition-colors">插入 (AND)</button>
                                    <button type="button" onclick="insertPointRule('OR')" class="flex-1 bg-[#2a2a28] hover:bg-[#3a3a38] text-[#b0aea5] text-[10px] py-1.5 rounded font-semibold transition-colors">插入 (OR)</button>
                                    <button type="button" onclick="insertPointRule('OVERWRITE')" class="flex-1 bg-[#d97757]/80 hover:bg-[#d97757] text-white text-[10px] py-1.5 rounded font-semibold transition-colors">插入覆蓋</button>
                                </div>
                            </div>
                            
                            <div class="space-y-3 pt-3 border-t border-[#b0aea5]/10">"""

if '<div class="space-y-3 pt-3 border-t border-[#b0aea5]/10">' in content and 'generator-pt1' not in content:
    content = content.replace('<div class="space-y-3 pt-3 border-t border-[#b0aea5]/10">', events_generator, 1)
    print("Fixed Events tab Point Generator")

# 3. Restore the Edit Modal Point ID helper
modal_generator = """            <!-- 點位規則產生器 -->
            <div class="bg-[#1a1a18] p-3 rounded-lg border border-[#b0aea5]/10 space-y-2">
                <label class="text-[10px] text-[#b0aea5] font-semibold block">🔗 點位規則產生器 (Point Rule Generator)</label>
                <div class="grid grid-cols-4 gap-2">
                    <input type="text" id="modal-pt1" placeholder="ID 1" class="bg-[#151513] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757] font-mono">
                    <input type="text" id="modal-pt2" placeholder="ID 2" class="bg-[#151513] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757] font-mono">
                    <select id="modal-op" class="bg-[#151513] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757]">
                        <option value="><">><</option>
                        <option value="<>"><></option>
                        <option value=">><<">>><<</option>
                    </select>
                    <input type="number" id="modal-num" value="20" placeholder="%" class="bg-[#151513] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757] font-mono">
                </div>
                <div class="flex gap-2">
                    <button type="button" onclick="modalInsertRule('AND')" class="flex-1 bg-[#2a2a28] hover:bg-[#3a3a38] text-[#b0aea5] text-[9px] py-1 rounded transition-colors">+ AND</button>
                    <button type="button" onclick="modalInsertRule('OR')" class="flex-1 bg-[#2a2a28] hover:bg-[#3a3a38] text-[#b0aea5] text-[9px] py-1 rounded transition-colors">+ OR</button>
                    <button type="button" onclick="modalInsertRule('OVERWRITE')" class="flex-1 bg-[#d97757]/80 hover:bg-[#d97757] text-white text-[9px] py-1 rounded transition-colors">覆蓋</button>
                </div>
            </div>"""

if '<!-- Point ID helper removed as requested -->' in content:
    content = content.replace('<!-- Point ID helper removed as requested -->', modal_generator)
    print("Fixed Edit Modal Point Generator")

# Also let's clean up the malformed chunk from my accidental replacement in Events tab.
malformed_chunk = """                            <!-- 點位對照與快速預設 -->
                            <div class="mb-4 bg-[#151513] p-4 rounded-xl border border-[#b0aea5]/10 space-y-3">
                                <div class="flex justify-between items-center cursor-pointer" onclick="toggleLandmarkRef()">
                                    <label class="text-xs text-[#b0aea5] font-semibold block cursor-pointer">🔗 點位對照與快速預設</label>
                                    <span class="text-[#b0aea5] text-xs">▼</span>
                                </div>
                                <div id="landmark-ref-panel" class="hidden space-y-3 pt-2">
                                    <div class="flex gap-4">
                                        <img src="https://mediapipe.dev/images/mobile/pose_tracking_full_body_landmarks.png" alt="Pose Landmarks" class="w-1/2 rounded-lg opacity-80 hover:opacity-100 transition-opacity">
                                        <img src="https://user-images.githubusercontent.com/37399864/112467332-9dfa5f80-8d9e-11eb-8c17-09a633ba20d2.png" alt="Face Landmarks" class="w-1/2 rounded-lg opacity-80 hover:opacity-100 transition-opacity bg-white/10">
                                    </div>
                                    <div class="space-y-2 pt-2 border-t border-[#b0aea5]/10">
                                        <label class="text-[10px] text-[#b0aea5]">快速帶入預設點位規則：</label>
                                        <div class="flex flex-wrap gap-1">
                                            <button type="button" onclick="setPresetPoints('p11', 'p12', '><', 15)" class="bg-[#1a1a18] hover:bg-[#2a2a28] text-[#b0aea5] hover:text-[#faf9f5] text-[9px] py-1 px-2 rounded border border-[#b0aea5]/10">
                                                肩寬縮小 (駝背)
                                            </button>
                                            <button type="button" onclick="setPresetPoints('p0', 'p11', '<>', 10)" class="bg-[#1a1a18] hover:bg-[#2a2a28] text-[#b0aea5] hover:text-[#faf9f5] text-[9px] py-1 px-2 rounded border border-[#b0aea5]/10">
                                                頭部前傾
                                            </button>
                                            <button type="button" onclick="setPresetPoints('f33', 'f263', '<>', 20)" class="bg-[#1a1a18] hover:bg-[#2a2a28] text-[#b0aea5] hover:text-[#faf9f5] text-[9px] py-1 px-2 rounded border border-[#b0aea5]/10">
                                                眼距放寬 (轉頭)
                                            </button>
                                            <button type="button" onclick="setPresetPoints('f13', 'f14', '<>', 25)" class="bg-[#1a1a18] hover:bg-[#2a2a28] text-[#b0aea5] hover:text-[#faf9f5] text-[9px] py-1 px-2 rounded border border-[#b0aea5]/10">
                                                嘴巴張開
                                            </button>
                                        </div>
                                    </div>
                                    <div class="space-y-3 pt-2 border-t border-[#b0aea5]/10">
                                        <label class="text-[10px] text-[#b0aea5] block">產生新點位規則並插入語法</label>
                                        <div class="grid grid-cols-2 gap-3">
                                            <div>
                                                <label class="text-[9px] text-[#706e68] block">點位 1 ID</label>
                                                <input type="text" id="generator-pt1" placeholder="例: f1" class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757] font-mono">
                                            </div>
                                            <div>
                                                <label class="text-[9px] text-[#706e68] block">點位 2 ID</label>
                                                <input type="text" id="generator-pt2" placeholder="例: f152" class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757] font-mono">
                                            </div>
                                        </div>
                                        <div class="grid grid-cols-2 gap-3">
                                            <div>
                                                <label class="text-[9px] text-[#706e68] block">變化方向</label>
                                                <select id="generator-op" class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757]">
                                                    <option value="><">>< 縮短 (Shrink)</option>
                                                    <option value="<>"><> 放大 (Expand)</option>
                                                    <option value=">><<">>><< 變化 (Both)</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label class="text-[9px] text-[#706e68] block">臨界比例 (%)</label>
                                                <input type="number" id="generator-num" value="20" min="1" max="100" class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded p-1.5 text-xs focus:outline-none focus:border-[#d97757] font-mono">
                                            </div>
                                        </div>
                                        <div class="flex gap-2">
                                            <button type="button" onclick="insertPointRule('AND')" class="flex-1 bg-[#2a2a28] hover:bg-[#3a3a38] text-[#b0aea5] text-[10px] py-1.5 rounded font-semibold transition-colors">插入 (AND)</button>
                                            <button type="button" onclick="insertPointRule('OR')" class="flex-1 bg-[#2a2a28] hover:bg-[#3a3a38] text-[#b0aea5] text-[10px] py-1.5 rounded font-semibold transition-colors">插入 (OR)</button>
                                            <button type="button" onclick="insertPointRule('OVERWRITE')" class="flex-1 bg-[#d97757]/80 hover:bg-[#d97757] text-white text-[10px] py-1.5 rounded font-semibold transition-colors">插入覆蓋</button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <input type="text" id="event-syntax" class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded-lg p-3 text-sm focus:outline-none focus:border-[#d97757] font-mono" placeholder="例如: slouch AND f1,f152 >< num=20%">"""
if malformed_chunk in content:
    content = content.replace(malformed_chunk, '<input type="text" id="event-syntax" required\n                                    class="w-full bg-[#1a1a18] border border-[#b0aea5]/20 text-[#faf9f5] rounded-lg p-2.5 text-xs focus:outline-none focus:border-[#d97757] font-mono"\n                                    placeholder="例如: slouch AND sway">')

with open('web/Monitor.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done patching.")
