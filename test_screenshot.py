from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        page.goto('http://localhost:8080/')
        page.wait_for_timeout(2000) # wait for page to render and fetch events
        page.screenshot(path='/Users/shihte.hsiao/.gemini/antigravity/brain/9e56045f-6de8-4bfb-b4a4-cf1923b81932/artifacts/test.png', full_page=True)
        print("Screenshot saved.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        browser.close()
