import re

with open('web/Monitor.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace everything from Point Trigger Generator Helper to Generated Syntax Preview
regex = re.compile(r'<!-- Point Trigger Generator Helper -->.*?<!-- Generated Syntax Preview -->', re.DOTALL)
html = regex.sub('<!-- Generated Syntax Preview -->', html)

# Make sure "skill-pt1" is gone just in case it's somewhere else
html = re.sub(r'<input[^>]*id="skill-pt[12]"[^>]*>', '', html)
html = re.sub(r'<select[^>]*id="skill-op"[^>]*>.*?</select>', '', html, flags=re.DOTALL)
html = re.sub(r'<input[^>]*id="skill-num"[^>]*>', '', html)

with open('web/Monitor.html', 'w', encoding='utf-8') as f:
    f.write(html)
