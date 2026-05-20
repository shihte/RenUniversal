from pydantic import BaseModel, Field
from typing import Optional, Tuple
import numpy as np

class CaptureConfig(BaseModel):
    src: int = Field(default=0, description="Camera source index")
    width: int = Field(default=1280, description="Target frame width")
    height: int = Field(default=720, description="Target frame height")
    fps_limit: Optional[int] = Field(default=None, description="Optional FPS limit")

class FrameData(BaseModel):
    class Config:
        arbitrary_types_allowed = True
    
    grabbed: bool
    frame: Optional[np.ndarray] = None
    timestamp: float
