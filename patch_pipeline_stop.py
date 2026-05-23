import re

with open('backend/core/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_stop = r"""    def stop\(self\):.*?if hasattr\(self, 'capture'\):.*?self\.capture\.stop\(\)"""
new_stop = r"""    def stop(self):
        \"\"\"
        停止代理流水線，釋放資源。
        \"\"\"
        logger.info("Stopping AgentPipeline workflow")
        if hasattr(self, 'captures'):
            for src, cap in self.captures.items():
                logger.info(f"Stopping camera {src}")
                cap.stop()
            self.captures.clear()"""

content = re.sub(old_stop, new_stop, content, flags=re.DOTALL)

with open('backend/core/pipeline.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated pipeline stop")
