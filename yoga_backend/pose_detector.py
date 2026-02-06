import cv2
import numpy as np
import os
from django.conf import settings
import logging
from .pose_detectors import get_pose_detector, is_pose_supported

logger = logging.getLogger(__name__)


class YogaPoseDetector:
    """
    Main yoga pose detection class that routes to specific pose detectors
    """
    
    def __init__(self):
        # Import MediaPipe here (lazy loading)
        try:
            import mediapipe as mp
            self.mp = mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            logger.info("MediaPipe Pose initialized successfully")
        except (ImportError, AttributeError) as e:
            logger.error(f"MediaPipe initialization failed: {e}")
            self.mp = None
            self.pose = None
        
        # Current pose detector
        self.current_detector = None
        self.current_pose = None
        
        # All available poses
        self.pose_classes = [
            'plank',
            'tree',
            'warrior2',
            'downdog',
            'goddess'
        ]
    
    def set_target_pose(self, pose_name):
        """
        Set the target pose and load appropriate detector
        """
        pose_name = pose_name.lower()
        
        if pose_name != self.current_pose:
            try:
                if is_pose_supported(pose_name):
                    self.current_detector = get_pose_detector(pose_name)
                    self.current_pose = pose_name
                    logger.info(f"Loaded detector for {pose_name}")
                else:
                    logger.warning(f"No specific detector for {pose_name}, using default")
                    self.current_detector = None
                    self.current_pose = pose_name
            except Exception as e:
                logger.error(f"Error loading detector for {pose_name}: {e}")
                self.current_detector = None
    
    def extract_keypoints(self, image):
        """
        Extract pose keypoints using MediaPipe
        """
        if not self.pose:
            logger.warning("MediaPipe Pose not initialized")
            return None, None
            
        try:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)
            
            logger.info(f"MediaPipe results: pose_landmarks = {results.pose_landmarks is not None}")
            
            if results.pose_landmarks:
                landmarks = []
                for landmark in results.pose_landmarks.landmark:
                    landmarks.extend([
                        landmark.x,
                        landmark.y,
                        landmark.z,
                        landmark.visibility
                    ])
                logger.info(f"Extracted {len(landmarks)} landmark values")
                return results, np.array(landmarks)
            else:
                logger.warning("No pose landmarks detected in frame")
            
            return results, None
        except Exception as e:
            logger.error(f"Error extracting keypoints: {e}", exc_info=True)
            return None, None
    
    def predict_pose(self, image, target_pose=None):
        """
        Predict yoga pose from image using specific detector
        """
        # Set target pose if provided
        if target_pose:
            logger.info(f"Setting target pose to: {target_pose}")
            self.set_target_pose(target_pose)
        
        # Extract keypoints
        logger.info("Extracting keypoints from image...")
        mp_results, keypoints = self.extract_keypoints(image)
        
        if keypoints is None or mp_results is None:
            logger.warning("Failed to extract keypoints - no pose detected")
            return {
                'success': False,
                'message': 'No pose detected',
                'pose': None,
                'confidence': 0
            }
        
        # Use specific detector if available
        if self.current_detector:
            logger.info(f"Using specific detector for {self.current_pose}")
            try:
                result = self.current_detector.detect(
                    mp_results,
                    image,
                    timestamp=0
                )
                
                logger.info(f"Detector result: stage={result.get('stage')}, is_correct={result.get('is_correct')}")
                
                return {
                    'success': True,
                    'pose': self.current_pose,
                    'stage': result.get('stage', 'unknown'),
                    'is_correct': result.get('is_correct', False),
                    'confidence': result.get('probability', 0),
                    'has_error': result.get('has_error', False),
                    'matches_target': result.get('is_correct', False),
                    'mode': 'specific_detector'
                }
            except Exception as e:
                logger.error(f"Error in specific detector: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': str(e)
                }
        
        # Fallback to demo mode if no specific detector
        logger.warning(f"No specific detector for {self.current_pose}, using demo mode")
        import random
        confidence = random.uniform(0.6, 0.95)
        return {
            'success': True,
            'pose': self.current_pose or random.choice(self.pose_classes),
            'confidence': confidence,
            'is_correct': confidence > 0.7,
            'mode': 'demo'
        }
    
    def process_frame(self, frame_data, target_pose=None):
        """
        Process base64 encoded frame
        """
        try:
            import base64
            
            logger.info(f"Processing frame - Target pose: {target_pose}")
            
            if not frame_data:
                logger.error("No frame data provided")
                return {
                    'success': False,
                    'message': 'No frame data provided'
                }
            
            if ',' in frame_data:
                frame_data = frame_data.split(',')[1]
            
            logger.info(f"Decoding frame data (length: {len(frame_data)})")
            
            img_data = base64.b64decode(frame_data)
            nparr = np.frombuffer(img_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Failed to decode image")
                return {
                    'success': False,
                    'message': 'Invalid image data'
                }
            
            logger.info(f"Image decoded successfully: shape={image.shape}")
            logger.info(f"Calling predict_pose with target: {target_pose}")
            
            result = self.predict_pose(image, target_pose)
            
            logger.info(f"Prediction result: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'pose') and self.pose:
            try:
                self.pose.close()
            except:
                pass


# Global instance
_detector_instance = None


def get_detector():
    """Get or create the global detector instance"""
    global _detector_instance
    if _detector_instance is None:
        logger.info("Creating new YogaPoseDetector instance")
        _detector_instance = YogaPoseDetector()
    return _detector_instance