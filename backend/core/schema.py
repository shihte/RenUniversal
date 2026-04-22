from pydantic import BaseModel, Field
from typing import Optional, Tuple

class DetectorStatus(BaseModel):
    """
    強型別姿勢檢測狀態模型。
    遵循 Google ADK Pattern: Strongly Typed I/O。
    """
    ratio: float = Field(0.0, description="Nose-chin ratio percentage")
    nose_chin_ratio: float = Field(0.0, description="Raw nose-chin ratio")
    is_bad_posture: bool = Field(False, description="Whether current posture is poor")
    down_count: int = Field(0, description="Total count of poor posture detected")
    fps: int = Field(0, description="Frames per second")
    connected: bool = Field(False, description="Webcam connection status")
    calibrating: bool = Field(True, description="Whether calibration is in progress")
    calibration_progress: int = Field(0, description="Calibration progress percentage (0-100)")
    is_turning: bool = Field(False, description="Whether the head is turning (yaw filtering)")
    baseline_eye_dist: float = Field(0.0, description="Calibrated baseline eye distance")
    threshold: float = Field(30.0, description="Detection threshold")
    yaw_tolerance: float = Field(20.0, description="Yaw tolerance threshold")
    is_active: bool = Field(True, description="Whether detection is active")
    latency_ms: int = Field(0, description="Inference latency in milliseconds")

class SettingsUpdate(BaseModel):
    """
    設置更新請求 Schema。
    """
    threshold: Optional[float] = None
    yaw_tolerance: Optional[float] = None

class ControlCommand(BaseModel):
    """
    控制指令請求 Schema。
    """
    active: bool
