import re

with open('web/camera.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Revert to HTTPS and 8443
content = content.replace("const localMobileUrl = `http://${localIp}:8080/mobile`;", "const localMobileUrl = `https://${localIp}:8443/mobile`;")

with open('web/camera.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Restored HTTPS")
