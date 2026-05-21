import re
line = "c6d48265cbc14a.lhr.life tunneled with tls termination, https://c6d48265cbc14a.lhr.life"
match = re.search(r'https://[a-zA-Z0-9-.]+\.lhr\.life', line)
if match:
    print("Match:", match.group(0))
else:
    print("No match")
