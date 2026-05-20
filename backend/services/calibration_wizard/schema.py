from pydantic import BaseModel, Field
from typing import List, Optional

class CalibrationResult(BaseModel):
    is_complete: bool
    progress: int = Field(0, ge=0, le=100)
    baseline_eye_dist: float = 0.0
    baseline_nc_dist: float = 0.0
    baseline_shoulder_width: float = 0.0
    baseline_shoulder_midpoint_x: float = 0.0
    baseline_shoulder_midpoint_y: float = 0.0
    message: str = ""
