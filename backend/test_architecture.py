from core import SharedState
from core.schema import DetectorStatus
from loguru import logger
import numpy as np

def test_state_and_schema():
    logger.info("Starting architecture validation test...")
    
    state = SharedState()
    
    # 驗證預設值
    status = state.get_status()
    assert isinstance(status, DetectorStatus)
    assert status.connected is False
    assert status.is_active is True
    
    # 驗證更新
    state.update_status(ratio=45.5, connected=True)
    new_status = state.get_status()
    assert new_status.ratio == 45.5
    assert new_status.connected is True
    
    # 驗證 Frame 更新
    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    state.update_frame(dummy_frame)
    frame_out = state.get_frame()
    assert frame_out.shape == (100, 100, 3)
    
    logger.success("Architecture validation test PASSED")

if __name__ == "__main__":
    test_state_and_schema()
