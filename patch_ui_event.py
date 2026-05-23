import re

with open('web/camera.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add event listeners script to camera.html just before the closing </body> tag
# if it doesn't already exist. Or better, just put it inside the DOMContentLoaded block.

event_logic = """
            // Add listeners for multi-camera checkboxes
            const camCheckboxes = document.querySelectorAll('.cam-chk');
            camCheckboxes.forEach(chk => {
                chk.addEventListener('change', function() {
                    const checkedBoxes = Array.from(camCheckboxes).filter(cb => cb.checked);
                    if (checkedBoxes.length > 5) {
                        alert("最多只能啟用 5 個鏡頭！");
                        this.checked = false;
                        return;
                    }
                    if (checkedBoxes.length < 1) {
                        alert("最少必須啟用 1 個鏡頭！");
                        this.checked = true;
                        return;
                    }
                    const sources = checkedBoxes.map(cb => cb.value);
                    updateSetting('camera_source', sources);
                });
            });
"""

# Let's insert it inside document.addEventListener('DOMContentLoaded', ...)
# find `setInterval(fetchSettings, 2000);` and put it after it
pattern = r"(setInterval\(fetchSettings, 2000\);)"
content = re.sub(pattern, r"\1\n" + event_logic, content)

with open('web/camera.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated JS event listeners")
