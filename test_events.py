from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Browser Error: {err.message}"))
        page.goto('http://localhost:8080/')
        page.wait_for_timeout(2000)
        page.evaluate("switchTab('events')")
        page.wait_for_timeout(2000)
        browser.close()

try:
    run()
except Exception as e:
    print(f"Failed to run playwright: {e}")
