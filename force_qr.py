import re

with open('web/camera.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'// Sync Tunnel Connection Info.*?if \(tunnelContainer\) \{.*?if \(data\.public_url\) \{.*?\} else \{.*?\}\n                \}', re.DOTALL)

new_block = """// Sync Tunnel Connection Info
                const tunnelContainer = document.getElementById('tunnel-info-container');
                if (tunnelContainer) {
                    // Always render Local QR
                    const localIp = data.local_ip || '127.0.0.1';
                    const localMobileUrl = `http://${localIp}:8080/mobile`; 
                    
                    const localLinkEl = document.getElementById('local-link');
                    if (localLinkEl) {
                        localLinkEl.href = localMobileUrl;
                        localLinkEl.textContent = localMobileUrl;
                        document.getElementById('local-qr').src = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(localMobileUrl)}`;
                    }

                    // Always show public block, but with a warning if not connected
                    const ptb = document.getElementById('public-tunnel-block'); 
                    if(ptb) ptb.classList.remove('hidden');

                    const linkEl = document.getElementById('tunnel-link');
                    if (data.public_url) {
                        const mobileUrl = `${data.public_url}/mobile`;
                        if (linkEl) {
                            linkEl.href = mobileUrl;
                            linkEl.textContent = mobileUrl;
                            document.getElementById('tunnel-qr').src = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(mobileUrl)}`;
                        }
                    } else {
                        if (linkEl) {
                            linkEl.href = "#";
                            linkEl.textContent = "未啟動 (Ngrok Not Running)";
                            document.getElementById('tunnel-qr').src = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=NotConnected`;
                        }
                    }
                }"""

if pattern.search(content):
    content = pattern.sub(new_block, content)
    with open('web/camera.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed camera.html")
else:
    print("Could not find pattern in camera.html")
