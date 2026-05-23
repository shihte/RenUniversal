import re

with open('backend/stream_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The first one is right before @app.route('/status')
# Let's find it.
old_api = r"""
@app.route\('/cameras'\)
def get_cameras\(\):.*?return jsonify\(\{"cameras": cameras\}\)
"""

# There are two matches. We will remove the first one.
matches = list(re.finditer(r"@app.route\('/cameras'\)\ndef get_cameras\(\):.*?return jsonify\(\{\"cameras\": cameras\}\)", content, re.DOTALL))
if len(matches) > 1:
    m = matches[0]
    content = content[:m.start()] + content[m.end():]

with open('backend/stream_server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed duplicate get_cameras")
