import glob

html_files = glob.glob('web/*.html')

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix null toggleEl, statusEl, liveIndicator, and stats
    content = content.replace("if (!toggleEl.matches(':active'))", "if (toggleEl && !toggleEl.matches(':active'))")
    content = content.replace("liveIndicator.className =", "if (liveIndicator) liveIndicator.className =")
    content = content.replace("statusEl.className =", "if (statusEl) statusEl.className =")
    content = content.replace("document.getElementById('fps-display').textContent =", "const fpsEl = document.getElementById('fps-display'); if (fpsEl) fpsEl.textContent =")
    content = content.replace("document.getElementById('ratio-value').textContent =", "const ratioEl = document.getElementById('ratio-value'); if (ratioEl) ratioEl.textContent =")
    content = content.replace("document.getElementById('latency-value').textContent =", "const latencyEl = document.getElementById('latency-value'); if (latencyEl) latencyEl.textContent =")

    # 2. Fix the QR code hiding logic in camera.html
    # In Monitor_backup.html, the public tunnel div looks like this:
    # <div class="space-y-2 p-4 rounded-lg bg-[#252523] border border-[#d97757]/20">
    #     <span class="text-xs font-bold text-[#d97757]">選項 B：遠端公網穿透連線
    content = content.replace(
        '<div class="space-y-2 p-4 rounded-lg bg-[#252523] border border-[#d97757]/20">\n                        <span class="text-xs font-bold text-[#d97757]">選項 B',
        '<div id="public-tunnel-block" class="space-y-2 p-4 rounded-lg bg-[#252523] border border-[#d97757]/20">\n                        <span class="text-xs font-bold text-[#d97757]">選項 B'
    )
    
    # And replace the JS logic
    content = content.replace(
        "tunnelContainer.classList.add('hidden');",
        "const ptb = document.getElementById('public-tunnel-block'); if(ptb) ptb.classList.add('hidden');"
    )
    content = content.replace(
        "tunnelContainer.classList.remove('hidden');",
        "const ptb = document.getElementById('public-tunnel-block'); if(ptb) ptb.classList.remove('hidden');"
    )

    # 3. Add auto-load logic based on filename
    load_logic = "setLang('zh-TW');\n        loadAvailableCameras();\n"
    basename = file_path.split('/')[-1]
    if basename == 'skills.html':
        load_logic += "        loadSkills();\n"
    elif basename == 'events.html':
        load_logic += "        loadEvents();\n"
        
    import re
    content = re.sub(
        r"setLang\('zh-TW'\);\s*loadAvailableCameras\(\);",
        load_logic.strip(),
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("All fixed")
