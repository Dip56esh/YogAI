import numpy as np
import os
from django.conf import settings


def extract_important_keypoints(mp_results, important_landmarks):
    """
    Extract important keypoints from mediapipe results
    """
    # Import mediapipe here to avoid module-level import issues
    import mediapipe as mp
    
    landmarks = mp_results.pose_landmarks.landmark
    
    data = []
    for lm_name in important_landmarks:
        lm_index = getattr(mp.solutions.pose.PoseLandmark, lm_name).value
        lm = landmarks[lm_index]
        data.extend([lm.x, lm.y, lm.z, lm.visibility])
    
    return data


def get_model_path(model_name):
    """
    Get full path to model file
    """
    return os.path.join(
        settings.BASE_DIR,
        'yoga_backend',
        'models',
        model_name
    )


def get_drawing_color(has_error):
    """
    Return colors for drawing based on error status
    
    Returns:
        landmark_color (tuple): BGR color for landmarks
        connection_color (tuple): BGR color for connections
    """
    if has_error:
        # Red color for errors
        landmark_color = (0, 0, 255)
        connection_color = (0, 0, 200)
    else:
        # Green color for correct
        landmark_color = (0, 255, 0)
        connection_color = (0, 200, 0)
    
    return landmark_color, connection_color