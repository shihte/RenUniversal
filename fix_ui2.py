import re

with open('web/Monitor.html', 'r', encoding='utf-8') as f:
    content = f.read()

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

target = '<div class="space-y-3 pt-3 border-t border-[#b0aea5]/10">'

if target in content and 'id="generator-pt1"' not in content:
    content = content.replace(target, events_generator, 1)
    print("Fixed Events tab Point Generator")

# Clean up malformed chunk from skills tab if it's there
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
                            </div>"""

if malformed_chunk in content:
    content = content.replace(malformed_chunk, '')
    print("Cleaned up malformed chunk from earlier")

with open('web/Monitor.html', 'w', encoding='utf-8') as f:
    f.write(content)
