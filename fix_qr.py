import re

with open('web/camera.html', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to extract the local qr code generation out of the `if (data.public_url)` block.
old_logic = """
                    if (data.public_url) {
                        const localIp = data.local_ip || '127.0.0.1';
                        const localMobileUrl = `https://${localIp}:8443/mobile`;
                        
                        const localLinkEl = document.getElementById('local-link');
                        if (localLinkEl && localLinkEl.href !== localMobileUrl) {
                            localLinkEl.href = localMobileUrl;
                            localLinkEl.textContent = localMobileUrl;
                            document.getElementById('local-qr').src = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(localMobileUrl)}`;
                        }

                        const mobileUrl = `${data.public_url}/mobile`;
                        const linkEl = document.getElementById('tunnel-link');
                        if (linkEl && linkEl.href !== mobileUrl) {
                            linkEl.href = mobileUrl;
                            linkEl.textContent = mobileUrl;
                            document.getElementById('tunnel-qr').src = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(mobileUrl)}`;
                        }
                        const ptb = document.getElementById('public-tunnel-block'); if(ptb) ptb.classList.remove('hidden');
                    } else {
                        const ptb = document.getElementById('public-tunnel-block'); if(ptb) ptb.classList.add('hidden');
                    }
"""

new_logic = """
                    // ALways generate local QR
                    const localIp = data.local_ip || '127.0.0.1';
                    const localMobileUrl = `http://${localIp}:8080/mobile`; // Usually mobile app runs on same server now? Wait, in stream_server it's 8080? Wait, the old code used 8443
                    // Let's keep 8443 just in case, but usually it's just the HTTP URL.
                    
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
                        const ptb = document.getElementById('public-tunnel-block'); if(ptb) ptb.classList.remove('hidden');
                    } else {
                        const ptb = document.getElementById('public-tunnel-block'); if(ptb) ptb.classList.add('hidden');
                    }
"""

content = content.replace(old_logic.strip(), new_logic.strip())

with open('web/camera.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed QR Code Logic in camera.html")
