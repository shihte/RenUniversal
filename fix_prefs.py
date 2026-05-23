import json

with open('preferences.json', 'r') as f:
    prefs = json.load(f)

prefs["camera_source"] = ["local_0"]

with open('preferences.json', 'w') as f:
    json.dump(prefs, f, indent=4)
print("Forced camera_source to ['local_0']")
