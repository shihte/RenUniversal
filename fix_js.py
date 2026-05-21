import os
import glob

html_files = glob.glob('web/*.html')

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Fix toggleEl null check
    content = content.replace("if (!toggleEl.matches(':active'))", "if (toggleEl && !toggleEl.matches(':active'))")
    
    # Auto-load logic based on filename
    # At the end of the file we have:
    # setLang('zh-TW');
    # loadAvailableCameras();
    # setInterval(fetchStatus, 100);
    
    load_logic = "setLang('zh-TW');\n        loadAvailableCameras();\n"
    
    basename = os.path.basename(file_path)
    if basename == 'skills.html':
        load_logic += "        loadSkills();\n"
    elif basename == 'events.html':
        load_logic += "        loadEvents();\n"
        
    # Replace the initialization block safely
    import re
    # Match the block
    content = re.sub(
        r"setLang\('zh-TW'\);\s*loadAvailableCameras\(\);",
        load_logic.strip(),
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("JS Fixed")
