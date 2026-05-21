import os
import json
import importlib.util
from loguru import logger
from typing import Dict, Any, Tuple, Optional

class ActionEngine:
    """
    動態動作判定引擎 (Dynamic Action Engine)
    負責掃描 root skills/ 目錄，動態載入各個動作判斷包，並在串流循環中執行判定。
    """
    
    def __init__(self, skills_dir: str):
        """
        初始化動作引擎。
        
        Args:
            skills_dir (str): 動作判斷包所在的根目錄路徑。
        """
        self.skills_dir = skills_dir
        self.detectors = {}
        self.load_action_skills()

    def load_action_skills(self):
        """
        掃描並動態載入 skills/ 目錄下的所有動作判斷包。
        """
        if not os.path.exists(self.skills_dir):
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return

        logger.info(f"Scanning directory {self.skills_dir} for action packages...")
        self.detectors.clear()
        
        for item in os.listdir(self.skills_dir):
            item_path = os.path.join(self.skills_dir, item)
            if os.path.isdir(item_path):
                config_path = os.path.join(item_path, "config.json")
                logic_path = os.path.join(item_path, "logic.py")
                
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = json.load(f)
                        
                        if not config.get("enabled", True):
                            logger.info(f"Action skill {item} is disabled in config.")
                            continue

                        if os.path.exists(logic_path):
                            # 動態載入 Python 模組
                            module_name = f"skills_{item}"
                            spec = importlib.util.spec_from_file_location(module_name, logic_path)
                            if spec is None or spec.loader is None:
                                continue
                                
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)

                            if hasattr(module, "ActionDetector"):
                                detector_class = getattr(module, "ActionDetector")
                                self.detectors[item] = detector_class(config)
                                logger.success(f"Successfully loaded Action Judgment Package: {config.get('name', item)} ({item})")
                            else:
                                logger.error(f"Module {item} logic.py does not define 'ActionDetector' class.")
                        else:
                            # Use generic skill detector for UI created skills
                            from backend.core.generic_skill_detector import GenericActionDetector
                            self.detectors[item] = GenericActionDetector(config)
                            logger.success(f"Successfully loaded Generic Action Judgment Package: {config.get('name', item)} ({item})")
                    except Exception as e:
                        logger.error(f"Failed to dynamically load action package {item}: {e}")

    def evaluate_all(self, 
                     face_landmarks: Any, 
                     pose_landmarks: Any, 
                     face_dim: Tuple[int, int],
                     body_dim: Tuple[int, int],
                     baselines: Dict[str, float], 
                     preferences: Dict[str, Any],
                     state_history: Dict[str, Any]) -> Dict[str, Tuple[bool, float, Dict[str, Any]]]:
        """
        對所有已載入的動作判斷包進行評估。
        
        Returns:
            Dict: 格式為 { "action_name": (is_triggered, metric_value, debug_info) }
        """
        results = {}
        for key, detector in self.detectors.items():
            try:
                is_triggered, metric_val, debug_info = detector.evaluate(
                    face_landmarks, pose_landmarks, face_dim, body_dim, baselines, preferences, state_history
                )
                results[key] = (is_triggered, metric_val, debug_info)
            except Exception as e:
                logger.error(f"Error running detector {key}: {e}")
                results[key] = (False, 0.0, {"error": str(e)})
        return results
