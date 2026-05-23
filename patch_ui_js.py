import re

with open('web/camera.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update initSettings
old_init = r"""                const cameraSelect = document\.getElementById\('camera-source-select'\);
                if \(cameraSelect && !cameraSelect\.matches\(':focus'\)\) \{
                    cameraSelect\.value = data\.camera_source \|\| 'local_0';
                \}"""

new_init = """                // Multi-camera checkboxes
                const camCheckboxes = document.querySelectorAll('.cam-chk');
                if (camCheckboxes.length > 0) {
                    let sources = data.camera_source;
                    // Backward compatibility if it's a string
                    if (typeof sources === 'string') {
                        if (sources === 'dual') sources = ['local_0', 'phone'];
                        else sources = [sources];
                    }
                    if (!Array.isArray(sources) || sources.length === 0) sources = ['local_0'];
                    
                    camCheckboxes.forEach(chk => {
                        chk.checked = sources.includes(chk.value);
                    });
                }"""

content = re.sub(old_init, new_init, content, flags=re.DOTALL)

with open('web/camera.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated JS initSettings")
