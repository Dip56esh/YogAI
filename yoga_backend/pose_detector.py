import cv2
import numpy as np
import mediapipe as mp
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class YogaPoseDetector:
    """
    Yoga pose detection using MediaPipe for keypoint extraction
    and a trained model for classification
    """
    
    def __init__(self):
        self.model = None
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Define yoga pose classes (update based on your model)
        self.pose_classes = [
            'downdog',
            'goddess', 
            'plank',
            'tree',
            'warrior2'
        ]
        
        self._load_model()
    
    def _load_model(self):
        """Load the trained yoga pose classification model"""
        try:
            from tensorflow import keras
            model_path = os.path.join(
                settings.BASE_DIR, 
                'yoga_backend', 
                'trained_models', 
                'yoga_model.h5'
            )
            
            if os.path.exists(model_path):
                self.model = keras.models.load_model(model_path)
                logger.info(f"Model loaded successfully from {model_path}")
            else:
                logger.warning(f"Model file not found at {model_path}")
                logger.warning("Pose detection will work in demo mode")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.warning("Running in demo mode without model")
    
    def extract_keypoints(self, image):
        """
        Extract pose keypoints using MediaPipe
        
        Args:
            image: OpenCV image (BGR format)
            
        Returns:
            numpy array of keypoints or None if no pose detected
        """
        try:
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process the image
            results = self.pose.process(image_rgb)
            
            if results.pose_landmarks:
                # Extract all landmarks
                landmarks = []
                for landmark in results.pose_landmarks.landmark:
                    landmarks.extend([
                        landmark.x,
                        landmark.y,
                        landmark.z,
                        landmark.visibility
                    ])
                return np.array(landmarks)
            
            return None
        except Exception as e:
            logger.error(f"Error extracting keypoints: {e}")
            return None
    
    def predict_pose(self, keypoints):
        """
        Predict yoga pose from keypoints
        
        Args:
            keypoints: numpy array of pose keypoints
            
        Returns:
            dict with prediction results
        """
        if self.model is None:
            # Demo mode - return random predictions for testing
            import random
            pose = random.choice(self.pose_classes)
            confidence = random.uniform(0.6, 0.95)
            return {
                'success': True,
                'pose': pose,
                'confidence': confidence,
                'is_correct': confidence > 0.7,
                'mode': 'demo'
            }
        
        try:
            # Reshape keypoints for model input
            keypoints_input = keypoints.reshape(1, -1)
            
            # Make prediction
            predictions = self.model.predict(keypoints_input, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class])
            
            # Get all prediction scores
            all_predictions = {
                self.pose_classes[i]: float(predictions[0][i])
                for i in range(len(self.pose_classes))
            }
            
            return {
                'success': True,
                'pose': self.pose_classes[predicted_class],
                'confidence': confidence,
                'is_correct': confidence > 0.7,
                'all_predictions': all_predictions,
                'mode': 'model'
            }
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_frame(self, frame_data):
        """
        Process a base64 encoded frame
        
        Args:
            frame_data: base64 encoded image string
            
        Returns:
            dict with detection results
        """
        try:
            import base64
            
            # Decode base64 image
            if ',' in frame_data:
                frame_data = frame_data.split(',')[1]
            
            img_data = base64.b64decode(frame_data)
            nparr = np.frombuffer(img_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {
                    'success': False,
                    'message': 'Invalid image data'
                }
            
            # Extract keypoints
            keypoints = self.extract_keypoints(image)
            
            if keypoints is None:
                return {
                    'success': False,
                    'message': 'No pose detected in frame'
                }
            
            # Predict pose
            result = self.predict_pose(keypoints)
            return result
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'pose'):
            self.pose.close()


# Global instance (singleton pattern)
_detector_instance = None

def get_detector():
    """Get or create the global detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = YogaPoseDetector()
    return _detector_instance