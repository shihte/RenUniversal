import re

with open('backend/stream_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_loop = r"""            # 如果偵測已啟動則執行流水線循環
            if state\.get_status\(\)\.is_active:.*?if dimmed is not None:
                    state\.update_frame\(dimmed\)"""

new_loop = """            # 執行流水線循環 (AI 與 暫停邏輯已在 pipeline 內處理)
            processed_frame = pipeline.run_cycle()
            if processed_frame is not None:
                state.update_frame(processed_frame)"""

content = re.sub(old_loop, new_loop, content, flags=re.DOTALL)

with open('backend/stream_server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated stream_server.py capture_loop")
