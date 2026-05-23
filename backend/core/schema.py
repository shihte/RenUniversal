from pydantic import BaseModel, Field
from typing import Optional, Tuple, Union, List

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
    sway_threshold: float = Field(15.0, description="Sway detection threshold percentage")
    lean_threshold: float = Field(10.0, description="Lean forward detection threshold percentage")
    is_active: bool = Field(True, description="Whether detection is active")
    latency_ms: int = Field(0, description="Inference latency in milliseconds")
    is_swaying: bool = Field(False, description="Whether the user is swaying")
    is_leaning_forward: bool = Field(False, description="Whether the user is leaning forward")
    sway_ratio: float = Field(0.0, description="Torso sway ratio percentage")
    lean_ratio: float = Field(0.0, description="Torso lean ratio percentage")
    camera_source: Union[str, List[str]] = Field("local_0", description="Selected camera source (local_0, local_1, phone, dual)")
    public_url: Optional[str] = Field(None, description="Public intranet tunnel URL")
    flip_enabled: bool = Field(True, description="Whether preview flipping is enabled")
    active_skills: dict = Field(default_factory=dict, description="States of all evaluated skills (e.g. {name: bool})")
    active_events: dict = Field(default_factory=dict, description="States of all evaluated compound event rules")
    metrics: dict = Field(default_factory=dict, description="Generic metrics calculated by active skills (e.g. {skill_name: float})")
    trigger_counts: dict = Field(default_factory=dict, description="Alert counts for all skills and events")

class SettingsUpdate(BaseModel):
    """
    設置更新請求 Schema。
    """
    threshold: Optional[float] = None
    yaw_tolerance: Optional[float] = None
    sway_threshold: Optional[float] = None
    lean_threshold: Optional[float] = None
    camera_source: Optional[Union[str, List[str]]] = None
    flip_enabled: Optional[bool] = None

class ControlCommand(BaseModel):
    """
    控制指令請求 Schema。
    """
    active: bool
