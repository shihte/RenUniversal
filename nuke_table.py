import re

with open('web/Monitor.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Match the div that starts with "偵測點位 ID 建構器" or similar if the user circled it
regex = re.compile(r'<!-- 點位對照與快速預設 -->.*?<!-- Preset Buttons -->', re.DOTALL)
html = regex.sub('', html)

# The user screenshot showed: "偵測點位 ID 建構器" with a button "點位 ID 對照表"
# And then "🔗 點位對照與快速預設"
# Let's just remove anything that matches 點位對照與快速預設 and its container
regex2 = re.compile(r'<div[^>]*>\s*<div[^>]*onclick="toggleLandmarkRef\(\)"[^>]*>.*?</div>.*?</div>.*?</div>\s*</div>', re.DOTALL)
# Wait, safer is to just find the string and remove its surrounding blocks.
