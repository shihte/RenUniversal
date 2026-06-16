from playwright.sync_api import sync_playwright
import time
import os
import shutil

app_data_dir = "/Users/shihte.hsiao/.gemini/antigravity-ide/brain/3f7657d0-4052-466f-ab29-a933ab3af8f2"
artifacts_dir = os.path.join(app_data_dir, "artifacts")
os.makedirs(artifacts_dir, exist_ok=True)
screenshot_path = os.path.join(artifacts_dir, "camera_view.png")

print(f"Taking screenshot to {screenshot_path}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://localhost:8080/')
    time.sleep(3)
    page.screenshot(path=screenshot_path)
    browser.close()

print("Screenshot captured successfully.")
