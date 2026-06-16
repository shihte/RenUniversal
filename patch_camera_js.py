import re

with open('web/camera.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove hardcoded checkboxes
old_html = r"""                    <div id="camera-checkboxes" class="flex flex-col gap-3 mt-2">.*?<p class="text-\[10px\]"""
new_html = r"""                    <div id="camera-checkboxes" class="flex flex-col gap-3 mt-2">
                        <!-- Dynamically populated -->
                    </div>
                    <p class="text-[10px]"""

content = re.sub(old_html, new_html, content, flags=re.DOTALL)

# Add loadCameras() to JS
js_code = """
        async function loadCameras() {
            try {
                const res = await fetch('/cameras');
                const data = await res.json();
                const container = document.getElementById('camera-checkboxes');
                container.innerHTML = '';
                
                const labels = {
                    'local_0': '💻 電腦預設鏡頭 (Local Camera 0)',
                    'local_1': '📹 外接相機 1 (Local Camera 1)',
                    'local_2': '📹 外接相機 2 (Local Camera 2)',
                    'phone': '📱 手機網路串流 (Mobile WiFi Stream)'
                };
                
                data.cameras.forEach(cam => {
                    const labelText = labels[cam] || `📹 未知相機 (${cam})`;
                    const html = `
                        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-lg bg-[#1a1a18] border border-[#b0aea5]/10 hover:border-[#d97757]/50 transition-colors">
                            <input type="checkbox" value="${cam}" class="cam-chk w-4 h-4 text-[#d97757] bg-[#252523] border-[#3a3a38] rounded focus:ring-[#d97757] focus:ring-2">
                            <span class="text-xs text-[#faf9f5]">${labelText}</span>
                        </label>
                    `;
                    container.insertAdjacentHTML('beforeend', html);
                });
                
                // Re-bind change events for new checkboxes
                document.querySelectorAll('.cam-chk').forEach(chk => {
                    chk.addEventListener('change', () => {
                        const checked = Array.from(document.querySelectorAll('.cam-chk:checked')).map(cb => cb.value);
                        if (checked.length > 5) {
                            chk.checked = false;
                            alert("最多只能選擇 5 個鏡頭！");
                            return;
                        }
                        if (checked.length === 0) {
                            chk.checked = true;
                            alert("最少必須選擇 1 個鏡頭！");
                            return;
                        }
                        updateSetting('camera_source', checked);
                    });
                });
            } catch (e) {
                console.error("Failed to load cameras", e);
            }
        }
"""

content = content.replace("async function updateSetting(", js_code + "\n        async function updateSetting(")

# Call loadCameras in DOMContentLoaded
content = content.replace("fetchStatus();", "await loadCameras();\n            fetchStatus();")
content = content.replace("setInterval(fetchStatus, 500);", "setInterval(fetchStatus, 500);\n            loadCameras();")
# wait, DOMContentLoaded is probably not async.
content = content.replace("document.addEventListener('DOMContentLoaded', () => {", "document.addEventListener('DOMContentLoaded', async () => {")

with open('web/camera.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated camera.html with dynamic cameras")
