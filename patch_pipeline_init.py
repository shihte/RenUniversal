import re

with open('backend/core/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace __init__
old_init = r"""    def __init__\(self, state: SharedState\):.*?self\.state = state.*?self\.capture = VideoCaptureSkill\(CaptureConfig\(src=0\)\)\.start\(\).*?self\.pose = mp_pose\.Pose\(.*?self\.face_mesh = mp_face_mesh\.FaceMesh\(""""
new_init = r"""    def __init__(self, state: SharedState):
        self.state = state
        self.captures = {} # dict of str -> VideoCaptureSkill
        
        # Action & Event Engines
        self.action_engine = ActionEngine()
        self.event_engine = EventEngine()
        
        # Initialize initial camera sources if provided
        initial_sources = self.state.get_status().camera_source
        if isinstance(initial_sources, str):
            if initial_sources == "dual": initial_sources = ["local_0", "phone"]
            else: initial_sources = [initial_sources]
            
        for src in initial_sources:
            if src.startswith("local_"):
                try: idx = int(src.split("_")[1])
                except: idx = 0
                if src not in self.captures:
                    self.captures[src] = VideoCaptureSkill(CaptureConfig(src=idx)).start()
        
        self.pose = mp_pose.Pose("""

content = re.sub(r'    def __init__\(self, state: SharedState\):.*?(?=self\.pose = mp_pose\.Pose\()', new_init, content, flags=re.DOTALL)

with open('backend/core/pipeline.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated pipeline init")
