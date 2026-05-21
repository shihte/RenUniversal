import re

with open('web/camera.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the tunnel connection block
pattern = re.compile(r'// Sync Tunnel Connection Info.*?if \(tunnelContainer\) \{.*?if \(data\.public_url\) \{.*?\} else \{.*?\}\n                \}', re.DOTALL)

new_block = """// Sync Tunnel Connection Info
                const tunnelContainer = document.getElementById('tunnel-info-container');
                if (tunnelContainer) {
                    // Always render Local QR
                    const localIp = data.local_ip || '127.0.0.1';
                    const localMobileUrl = `http://${localIp}:8080/mobile`; // Changed to HTTP since we might not have HTTPS locally
                    
                    const localLinkEl = document.getElementById('local-link');
                    if (localLinkEl && localLinkEl.href !== localMobileUrl) {
                        localLinkEl.href = localMobileUrl;
                        localLinkEl.textContent = localMobileUrl;
                        document.getElementById('local-qr').src = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(localMobileUrl)}`;
                    }

                    if (data.public_url) {
                        const mobileUrl = `${data.public_url}/mobile`;
                        const linkEl = document.getElementById('tunnel-link');
                        if (linkEl && linkEl.href !== mobileUrl) {
                            linkEl.href = mobileUrl;
                            linkEl.textContent = mobileUrl;
                            document.getElementById('tunnel-qr').src = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(mobileUrl)}`;
                        }
                        const ptb = document.getElementById('public-tunnel-block'); 
                        if(ptb) ptb.classList.remove('hidden');
                    } else {
                        const ptb = document.getElementById('public-tunnel-block'); 
                        if(ptb) ptb.classList.add('hidden');
                    }
                }"""

content = pattern.sub(new_block, content)

with open('web/camera.html', 'w', encoding='utf-8') as f:
    f.write(content)

# Fix game.html
with open('web/game.html', 'r', encoding='utf-8') as f:
    game_content = f.read()

game_pattern = re.compile(r'let currentTriggerCount = 0;.*?currentTriggerCount = data\.down_count;\n                    \}', re.DOTALL)

game_new_block = """let currentTriggerCount = 0;
                    if (data.trigger_counts && data.trigger_counts['ctar_tuck'] !== undefined) {
                        currentTriggerCount = data.trigger_counts['ctar_tuck'];
                    } else if (data.down_count !== undefined) {
                        currentTriggerCount = data.down_count;
                    }"""

game_content = game_pattern.sub(game_new_block, game_content)

with open('web/game.html', 'w', encoding='utf-8') as f:
    f.write(game_content)

print("Fixed both!")
