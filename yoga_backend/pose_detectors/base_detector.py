import cv2
import numpy as np
from abc import ABC, abstractmethod


class BasePoseDetector(ABC):
    """
    Base class for all pose detectors
    """
    
    def __init__(self):
        self.previous_stage = "unknown"
        self.results = []
        self.has_error = False
        
        # Import MediaPipe here (lazy loading)
        try:
            import mediapipe as mp
            self.mp = mp
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
        except (ImportError, AttributeError) as e:
            raise Exception(f"MediaPipe not available: {e}. Please install with: pip install mediapipe==0.10.9")
        
        self.init_important_landmarks()
        self.load_machine_learning_model()
    
    @abstractmethod
    def init_important_landmarks(self):
        """
        Define important landmarks for this pose
        Must be implemented by each pose detector
        """
        pass
    
    @abstractmethod
    def load_machine_learning_model(self):
        """
        Load the machine learning model for this pose
        Must be implemented by each pose detector
        """
        pass
    
    @abstractmethod
    def detect(self, mp_results, image, timestamp):
        """
        Detect pose and errors
        Must be implemented by each pose detector
        """
        pass
    
    def clear_results(self):
        """
        Clear detection results
        """
        self.previous_stage = "unknown"
        self.results = []
        self.has_error = False
    
    def get_current_stage(self):
        """
        Get current detection stage
        """
        return self.previous_stage
    
    def has_errors(self):
        """
        Check if current pose has errors
        """
        return self.has_error