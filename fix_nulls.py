import glob

html_files = glob.glob('web/*.html')

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # liveIndicator
    content = content.replace("liveIndicator.className =", "if (liveIndicator) liveIndicator.className =")
    content = content.replace("statusEl.className =", "if (statusEl) statusEl.className =")
    
    # Stats
    content = content.replace("document.getElementById('fps-display').textContent =", "const fpsEl = document.getElementById('fps-display'); if (fpsEl) fpsEl.textContent =")
    content = content.replace("document.getElementById('ratio-value').textContent =", "const ratioEl = document.getElementById('ratio-value'); if (ratioEl) ratioEl.textContent =")
    content = content.replace("document.getElementById('latency-value').textContent =", "const latencyEl = document.getElementById('latency-value'); if (latencyEl) latencyEl.textContent =")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Nulls Fixed")
