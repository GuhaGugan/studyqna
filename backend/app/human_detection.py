import cv2
import numpy as np
from PIL import Image
try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    YOLO = None
    ULTRALYTICS_AVAILABLE = False
    print("⚠️ Warning: ultralytics not available. Human detection will be disabled.")
import os
from typing import Tuple, Optional

# Load YOLO model for person detection
_model_path = os.path.join(os.path.dirname(__file__), "models", "yolov8n.pt")
_model = None

def get_model():
    """Lazy load YOLO model"""
    global _model
    if _model is None:
        try:
            _model = YOLO("yolov8n.pt")  # nano model for speed
        except Exception as e:
            print(f"Warning: Could not load YOLO model: {e}")
            print("Human detection will be disabled. Install ultralytics: pip install ultralytics")
    return _model

def detect_humans(image_path: str) -> Tuple[bool, Optional[str]]:
    """
    Detect if image contains humans (person class in YOLO)
    Returns: (has_humans, error_message)
    """
    try:
        model = get_model()
        if model is None:
            # If model not available, skip detection (for development)
            return False, None
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return False, "Could not read image"
        
        # Run detection
        results = model(img, classes=[0])  # class 0 is 'person' in COCO dataset
        
        # Check if any person detected
        has_humans = False
        for result in results:
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                # Check for person class (class 0)
                for box in boxes:
                    cls = int(box.cls[0])
                    if cls == 0:  # person class
                        has_humans = True
                        break
                if has_humans:
                    break
        
        if has_humans:
            return True, "Image contains human body — upload text-only or remove people."
        
        return False, None
        
    except Exception as e:
        # On error, be conservative and block
        print(f"Human detection error: {e}")
        return True, f"Safety check failed: {str(e)}"

def check_image_quality(image_path: str) -> Tuple[bool, Optional[str]]:
    """
    Check if image is readable (not too blurry)
    Returns: (is_readable, error_message)
    """
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return False, "Could not read image"
        
        # Calculate Laplacian variance (blur detection)
        laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
        
        # Threshold for blur detection (adjust as needed)
        if laplacian_var < 100:
            return False, "Image not readable. Retake closer and clearer photo."
        
        return True, None
        
    except Exception as e:
        return False, f"Quality check failed: {str(e)}"


