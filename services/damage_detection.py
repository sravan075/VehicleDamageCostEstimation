"""
Damage detection service using YOLO models
"""
import cv2
import numpy as np
from ultralytics import YOLO
from config.settings import DAMAGE_MODEL_PATH, SEVERITY_MODEL_PATH

# Load models
damage_model = YOLO(DAMAGE_MODEL_PATH)
severity_model = YOLO(SEVERITY_MODEL_PATH)

def detect_damage(image):
    """
    Detect damage and severity in an image
    
    Args:
        image: numpy array of the image
        
    Returns:
        tuple: (detected_damage, detected_severity, labeled_image) or (None, None, None)
    """
    damage_results = damage_model.predict(source=image, imgsz=640, conf=0.5, save=False)
    severity_results = severity_model.predict(source=image, imgsz=640, conf=0.5, save=False)
    
    if len(damage_results[0].boxes.cls) > 0 and len(severity_results[0].boxes.cls) > 0:
        detected_damage = damage_model.names[int(damage_results[0].boxes.cls[0])]
        detected_severity = severity_model.names[int(severity_results[0].boxes.cls[0])]
        
        # Create labeled image
        labeled_image = image.copy()
        for box in damage_results[0].boxes.xyxy:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(labeled_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(labeled_image, detected_damage, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        return detected_damage, detected_severity, labeled_image
    
    return None, None, None

