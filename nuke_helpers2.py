import re

with open('web/Monitor.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the ID Inputs in skills tab
regex = re.compile(r'<!-- ID Inputs -->.*?</div>\s*</div>', re.DOTALL)
html = regex.sub('', html)

# Remove the modal Point Rule Generator (if my previous script missed it)
regex2 = re.compile(r'<!-- 點位規則產生器 -->.*?</div>\s*</div>', re.DOTALL)
html = regex2.sub('', html)

with open('web/Monitor.html', 'w', encoding='utf-8') as f:
    f.write(html)
