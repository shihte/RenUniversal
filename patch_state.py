import re

with open('backend/core/state.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = r'            if "camera_source" in new_prefs:\n                current_dict\["camera_source"\] = str\(new_prefs\["camera_source"\]\)'
new_code = r"""            if "camera_source" in new_prefs:
                src = new_prefs["camera_source"]
                if isinstance(src, list):
                    current_dict["camera_source"] = [str(x) for x in src]
                else:
                    current_dict["camera_source"] = str(src)"""

content = re.sub(old_code, new_code, content)

with open('backend/core/state.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated state.py")
