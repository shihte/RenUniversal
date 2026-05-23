import re

with open('web/camera.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the space-y-4 div containing the select
old_html = r"""                <div class="space-y-4">
                    <label class="text-xs text-\[\#b0aea5\] font-medium">請選擇作用中的鏡頭裝置：</label>
                    <select id="camera-source-select".*?</select>
                    <p class="text-\[10px\] text-\[\#706e68\] leading-relaxed italic" data-i18n="camera_source_desc" id="camera-source-desc">
                        在手機上開啟手機串流網頁發送畫面，並在此選擇手機網路串流或雙鏡頭連線模式。
                    </p>
                </div>"""

new_html = """                <div class="space-y-4">
                    <label class="text-xs text-[#b0aea5] font-medium">請選擇作用中的鏡頭裝置 (最少 1，最多 5)：</label>
                    <div id="camera-checkboxes" class="flex flex-col gap-3 mt-2">
                        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-lg bg-[#1a1a18] border border-[#b0aea5]/10 hover:border-[#d97757]/50 transition-colors">
                            <input type="checkbox" value="local_0" class="cam-chk w-4 h-4 text-[#d97757] bg-[#252523] border-[#3a3a38] rounded focus:ring-[#d97757] focus:ring-2">
                            <span class="text-xs text-[#faf9f5]">💻 電腦預設鏡頭 (Local Camera 0)</span>
                        </label>
                        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-lg bg-[#1a1a18] border border-[#b0aea5]/10 hover:border-[#d97757]/50 transition-colors">
                            <input type="checkbox" value="local_1" class="cam-chk w-4 h-4 text-[#d97757] bg-[#252523] border-[#3a3a38] rounded focus:ring-[#d97757] focus:ring-2">
                            <span class="text-xs text-[#faf9f5]">📹 外接相機 1 (Local Camera 1)</span>
                        </label>
                        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-lg bg-[#1a1a18] border border-[#b0aea5]/10 hover:border-[#d97757]/50 transition-colors">
                            <input type="checkbox" value="local_2" class="cam-chk w-4 h-4 text-[#d97757] bg-[#252523] border-[#3a3a38] rounded focus:ring-[#d97757] focus:ring-2">
                            <span class="text-xs text-[#faf9f5]">📹 外接相機 2 (Local Camera 2)</span>
                        </label>
                        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-lg bg-[#1a1a18] border border-[#b0aea5]/10 hover:border-[#d97757]/50 transition-colors">
                            <input type="checkbox" value="local_3" class="cam-chk w-4 h-4 text-[#d97757] bg-[#252523] border-[#3a3a38] rounded focus:ring-[#d97757] focus:ring-2">
                            <span class="text-xs text-[#faf9f5]">📹 外接相機 3 (Local Camera 3)</span>
                        </label>
                        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-lg bg-[#1a1a18] border border-[#b0aea5]/10 hover:border-[#d97757]/50 transition-colors">
                            <input type="checkbox" value="phone" class="cam-chk w-4 h-4 text-[#d97757] bg-[#252523] border-[#3a3a38] rounded focus:ring-[#d97757] focus:ring-2">
                            <span class="text-xs text-[#faf9f5]">📱 手機網路串流 (Mobile WiFi Stream)</span>
                        </label>
                    </div>
                    <p class="text-[10px] text-[#706e68] leading-relaxed italic" data-i18n="camera_source_desc" id="camera-source-desc">
                        多鏡頭模式會自動分割畫面 (Grid Layout)。若選擇手機網路串流，請確保手機已掃描下方 QR Code 進行連線。
                    </p>
                </div>"""

content = re.sub(old_html, new_html, content, flags=re.DOTALL)
with open('web/camera.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced select with checkboxes")
