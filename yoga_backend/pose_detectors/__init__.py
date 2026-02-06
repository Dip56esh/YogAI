from .plank_detector import PlankDetector
# Import other detectors as you create them
# from .tree_detector import TreeDetector
# from .warrior2_detector import Warrior2Detector

# Detector registry
POSE_DETECTORS = {
    'plank': PlankDetector,
    # 'tree': TreeDetector,
    # 'warrior2': Warrior2Detector,
    # Add more as you create them
}


def get_pose_detector(pose_name):
    """
    Factory function to get the appropriate detector for a pose
    
    Args:
        pose_name (str): Name of the pose (e.g., 'plank', 'tree')
    
    Returns:
        BasePoseDetector: Instance of the appropriate detector
    
    Raises:
        ValueError: If pose detector is not found
    """
    pose_name = pose_name.lower()
    
    if pose_name not in POSE_DETECTORS:
        raise ValueError(f"No detector found for pose: {pose_name}")
    
    detector_class = POSE_DETECTORS[pose_name]
    return detector_class()


def is_pose_supported(pose_name):
    """
    Check if a pose has a dedicated detector
    
    Args:
        pose_name (str): Name of the pose
    
    Returns:
        bool: True if detector exists, False otherwise
    """
    return pose_name.lower() in POSE_DETECTORS