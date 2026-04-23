from pydantic import BaseModel, Field
from typing import Optional, List, Tuple

class PostureMetrics(BaseModel):
    eye_dist: float
    nose_chin_dist: float
    nc_ratio: float
    is_turning: bool
    is_bad_posture: bool

class PostureReport(BaseModel):
    is_valid: bool
    metrics: Optional[PostureMetrics] = None
    timestamp: float
    error_message: Optional[str] = None
