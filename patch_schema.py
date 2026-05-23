import re

with open('backend/core/schema.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Union to typing
if 'from typing import Optional, Tuple, Union, List' not in content:
    content = content.replace('from typing import Optional, Tuple', 'from typing import Optional, Tuple, Union, List')

# Update DetectorStatus
content = re.sub(r'camera_source: str = Field\(', 'camera_source: Union[str, List[str]] = Field(', content)

# Update SettingsUpdate
content = re.sub(r'camera_source: Optional\[str\] = None', 'camera_source: Optional[Union[str, List[str]]] = None', content)

with open('backend/core/schema.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated schema.py")
