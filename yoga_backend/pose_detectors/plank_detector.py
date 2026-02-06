import cv2
import numpy as np
import pandas as pd
import pickle
from .base_detector import BasePoseDetector
from ..utils import extract_important_keypoints, get_model_path, get_drawing_color


class PlankDetector(BasePoseDetector):
    PREDICTION_PROBABILITY_THRESHOLD = 0.6

    def init_important_landmarks(self):
        """
        Determine important landmarks for plank detection
        """
        self.important_landmarks = [
            "NOSE",
            "LEFT_SHOULDER",
            "RIGHT_SHOULDER",
            "LEFT_ELBOW",
            "RIGHT_ELBOW",
            "LEFT_WRIST",
            "RIGHT_WRIST",
            "LEFT_HIP",
            "RIGHT_HIP",
            "LEFT_KNEE",
            "RIGHT_KNEE",
            "LEFT_ANKLE",
            "RIGHT_ANKLE",
            "LEFT_HEEL",
            "RIGHT_HEEL",
            "LEFT_FOOT_INDEX",
            "RIGHT_FOOT_INDEX",
        ]

        # Generate all columns of the data frame
        self.headers = ["label"]
        for lm in self.important_landmarks:
            self.headers += [
                f"{lm.lower()}_x",
                f"{lm.lower()}_y",
                f"{lm.lower()}_z",
                f"{lm.lower()}_v",
            ]

    def load_machine_learning_model(self):
        """
        Load machine learning model for plank detection
        """
        try:
            model_path = get_model_path("plank_model.pkl")
            scaler_path = get_model_path("plank_input_scaler.pkl")
            
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            with open(scaler_path, "rb") as f:
                self.input_scaler = pickle.load(f)
        except Exception as e:
            raise Exception(f"Error loading plank model: {e}")

    def detect(self, mp_results, image, timestamp):
        """
        Detect plank pose and errors
        """
        try:
            # Extract keypoints from frame
            row = extract_important_keypoints(mp_results, self.important_landmarks)
            X = pd.DataFrame([row], columns=self.headers[1:])
            X = pd.DataFrame(self.input_scaler.transform(X))

            # Make prediction
            predicted_class = self.model.predict(X)[0]
            prediction_probability = self.model.predict_proba(X)[0]
            max_prob = prediction_probability[prediction_probability.argmax()]

            # Evaluate prediction
            if predicted_class == "C" and max_prob >= self.PREDICTION_PROBABILITY_THRESHOLD:
                current_stage = "correct"
            elif predicted_class == "L" and max_prob >= self.PREDICTION_PROBABILITY_THRESHOLD:
                current_stage = "low back"
            elif predicted_class == "H" and max_prob >= self.PREDICTION_PROBABILITY_THRESHOLD:
                current_stage = "high back"
            else:
                current_stage = "unknown"

            # Stage management
            if current_stage in ["low back", "high back"]:
                if self.previous_stage != current_stage:
                    self.results.append({
                        "stage": current_stage,
                        "timestamp": timestamp,
                        "probability": float(max_prob)
                    })
                    self.has_error = True
            else:
                self.has_error = False

            self.previous_stage = current_stage

            # Visualization
            landmark_color, connection_color = get_drawing_color(self.has_error)
            
            # Use mp_drawing from instance (loaded in __init__)
            self.mp_drawing.draw_landmarks(
                image,
                mp_results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=landmark_color, thickness=2, circle_radius=2),
                self.mp_drawing.DrawingSpec(color=connection_color, thickness=2, circle_radius=1),
            )

            # Status box
            cv2.rectangle(image, (0, 0), (250, 60), (245, 117, 16), -1)

            # Display probability
            cv2.putText(image, "PROB", (15, 12), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(round(max_prob, 2)), (10, 40), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            # Display class
            cv2.putText(image, "CLASS", (95, 12), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, current_stage, (90, 40), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            return {
                'stage': current_stage,
                'is_correct': current_stage == "correct",
                'probability': float(max_prob),
                'has_error': self.has_error
            }

        except Exception as e:
            raise Exception(f"Error while detecting plank: {e}")