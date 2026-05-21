import re

with open('web/Monitor.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Clean up Create Skill Form (Tab 3)
# We need to remove the entire section from <!-- 點位對照與快速預設 --> to the end of <!-- ID Inputs -->
# And just leave the "產生的語法（可手動修改）" (but rename it to just "觸發邏輯語法 (Rule Syntax)")
skills_tab_regex = re.compile(r'<!-- 點位對照與快速預設 -->.*?<!-- Generated Syntax Preview -->', re.DOTALL)
html = skills_tab_regex.sub(r'<!-- Rule Syntax Input -->\n', html)

# Rename "產生的語法（可手動修改）" to "觸發邏輯語法 (Rule Syntax) *"
html = html.replace('<label class="text-[10px] text-[#b0aea5] font-semibold block">產生的語法（可手動修改）</label>', 
                    '<label class="text-[10px] text-[#b0aea5] font-semibold block">觸發邏輯語法 (Rule Syntax) <span class="text-[#d97757]">*</span></label>')
html = html.replace('placeholder="填寫上方點位 ID 後自動產生"', 'placeholder="例如: f1,f152 >< num=20% 或 torso_lean > lean_threshold"')
html = html.replace('<p class="text-[9px] text-[#706e68]">格式：<code>f1,f152 >< num=20%</code>　說明：點位1,點位2 方向 num=閾值%</p>', 
                    '<p class="text-[9px] text-[#706e68]">請直接填寫判斷語法。支持點位運算 (例: <code>f1,f152 >< num=20%</code>) 或變數運算 (例: <code>torso_lean > 15</code>)。</p>')

# 2. Clean up Create Event Form (Tab 4)
# We need to remove the <!-- Point ID Generator --> completely.
events_generator_regex = re.compile(r'<!-- Point ID Generator -->.*?<div class="space-y-3 pt-3 border-t border-\[#b0aea5\]/10">', re.DOTALL)
html = events_generator_regex.sub(r'<div class="space-y-3 pt-3 border-t border-[#b0aea5]/10">', html)

# 3. Clean up Edit Modal
# Remove the <!-- 點位規則產生器 --> section
modal_generator_regex = re.compile(r'<!-- 點位規則產生器 -->.*?</div>\s*</div>', re.DOTALL)
html = modal_generator_regex.sub('', html)

# 4. Clean up Javascript functions
functions_to_remove = [
    r'function buildSkillSyntax\(\) \{.*?\n        \}',
    r'function setSkillPreset\(.*?\) \{.*?\n        \}',
    r'function toggleSkillLandmarkRef\(\) \{.*?\n        \}',
    r'function toggleLandmarkRef\(\) \{.*?\n        \}',
    r'function setPresetPoints\(.*?\) \{.*?\n        \}',
    r'function insertPointRule\(.*?\) \{.*?\n        \}',
    r'function modalInsertRule\(.*?\) \{.*?\n        \}'
]

for func_regex in functions_to_remove:
    html = re.sub(func_regex, '', html, flags=re.DOTALL)

with open('web/Monitor.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Nuked all ID helpers.")
