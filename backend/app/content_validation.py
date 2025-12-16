"""
Enhanced Content Validation System
Blocks inappropriate content and only allows study materials
"""
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
import os
import re
from typing import Tuple, Optional, List, Dict
import pytesseract

# Load YOLO model for object detection
_model_path = os.path.join(os.path.dirname(__file__), "models", "yolov8n.pt")
_model = None

# COCO class names (YOLO uses COCO dataset)
COCO_CLASSES = {
    0: 'person',
    1: 'bicycle', 2: 'car', 3: 'motorcycle', 4: 'airplane', 5: 'bus', 6: 'train', 7: 'truck',
    14: 'bird', 15: 'cat', 16: 'dog', 17: 'horse', 18: 'sheep', 19: 'cow',
    24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase',
    39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife', 44: 'spoon',
    46: 'bowl', 47: 'banana', 48: 'apple', 49: 'sandwich', 50: 'orange',
    62: 'chair', 63: 'couch', 64: 'potted plant', 65: 'bed', 66: 'dining table',
    67: 'toilet', 68: 'tv', 69: 'laptop', 70: 'mouse', 71: 'remote', 72: 'keyboard',
    73: 'cell phone', 74: 'microwave', 75: 'oven', 76: 'toaster', 77: 'sink',
    78: 'refrigerator', 79: 'book', 80: 'clock', 81: 'vase', 82: 'scissors',
    83: 'teddy bear', 84: 'hair drier', 85: 'toothbrush'
}

# Blocked classes (violence, weapons, etc.)
BLOCKED_CLASSES = {
    0: 'person',  # Human body
    43: 'knife',  # Weapon
    46: 'bowl',  # Could be used for violence
    82: 'scissors'  # Could be weapon
}

# Keywords that indicate blocked content
BLOCKED_KEYWORDS = [
    # Violence/Weapons
    'gun', 'pistol', 'rifle', 'weapon', 'knife', 'sword', 'blood', 'injury', 'wound',
    'violence', 'fight', 'attack', 'kill', 'murder', 'death', 'corpse',
    
    # Sexual content
    'nude', 'naked', 'sex', 'sexual', 'porn', 'pornography', 'erotic', 'explicit',
    'genital', 'breast', 'penis', 'vagina',
    
    # Medical/Anatomical
    'anatomy', 'skeleton', 'bone', 'organ', 'surgery', 'medical procedure',
    'x-ray', 'ct scan', 'mri', 'operation',
    
    # PII/IDs
    'passport', 'id card', 'driver license', 'ssn', 'social security',
    'credit card', 'bank account', 'signature', 'certificate', 'diploma',
    'birth certificate', 'aadhaar', 'pan card'
]

# Allowed keywords (study materials)
ALLOWED_KEYWORDS = [
    'textbook', 'book', 'page', 'chapter', 'section', 'lesson',
    'diagram', 'chart', 'graph', 'table', 'figure', 'illustration',
    'formula', 'equation', 'problem', 'solution', 'exercise',
    'question', 'answer', 'note', 'notes', 'study', 'material',
    'mathematics', 'physics', 'chemistry', 'biology', 'history',
    'geography', 'science', 'literature', 'grammar', 'vocabulary'
]

def get_model():
    """Lazy load YOLO model with PyTorch 2.6+ compatibility"""
    global _model
    if _model is None:
        try:
            print("📦 Loading YOLO model for content validation...")
            
            # Fix for PyTorch 2.6+ weights_only issue
            import torch
            import torch.serialization
            
            # Add ultralytics classes to safe globals for PyTorch 2.6+
            try:
                from ultralytics.nn.tasks import DetectionModel
                from ultralytics.nn.modules import Conv, Bottleneck, C2f, SPPF, Detect
                # Add all ultralytics classes that might be needed
                torch.serialization.add_safe_globals([
                    DetectionModel,
                    Conv, Bottleneck, C2f, SPPF, Detect
                ])
                print("✅ Added ultralytics classes to safe globals")
            except ImportError as ie:
                print(f"⚠️ Could not import ultralytics classes: {ie}")
                # Try to add them dynamically if possible
                try:
                    import ultralytics
                    # Get all classes from ultralytics.nn
                    for module_name in ['tasks', 'modules']:
                        try:
                            module = __import__(f'ultralytics.nn.{module_name}', fromlist=[''])
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if isinstance(attr, type) and attr.__module__.startswith('ultralytics'):
                                    torch.serialization.add_safe_globals([attr])
                        except:
                            pass
                except:
                    pass
            
            # Load model - YOLO should now work with safe globals
            _model = YOLO("yolov8n.pt")  # nano model for speed
            print("✅ YOLO model loaded successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not load YOLO model: {e}")
            print("⚠️ Trying monkey-patch method for PyTorch 2.6+...")
            
            # Alternative: Monkey-patch torch.load to use weights_only=False
            try:
                import torch
                original_load = torch.load
                
                def patched_load(*args, **kwargs):
                    # Force weights_only=False for YOLO models
                    if 'weights_only' not in kwargs:
                        kwargs['weights_only'] = False
                    return original_load(*args, **kwargs)
                
                torch.load = patched_load
                _model = YOLO("yolov8n.pt")
                # Restore original
                torch.load = original_load
                print("✅ YOLO model loaded with monkey-patch method")
            except Exception as e2:
                print(f"⚠️ Alternative loading also failed: {e2}")
                print("⚠️ Human detection will be limited. Content validation will use other methods (face detection, skin detection, OCR).")
                _model = None
    return _model

def detect_blocked_objects(image_path: str) -> Tuple[bool, Optional[str], List[str]]:
    """
    Detect blocked objects using YOLO
    Returns: (has_blocked, error_message, detected_classes)
    """
    try:
        model = get_model()
        if model is None:
            # If model not available, we still check other methods
            print("⚠️ YOLO model not available, skipping object detection")
            return False, None, []
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return True, "Could not read image", []
        
        # Resize image for faster processing (max 640px on longest side)
        height, width = img.shape[:2]
        max_dim = 640
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
            print(f"📐 Resized image from {width}x{height} to {new_width}x{new_height} for faster processing")
        
        # Run detection on all classes
        results = model(img, verbose=False)  # Disable verbose output for speed
        
        detected_classes = []
        blocked_detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Only consider high-confidence detections
                    if conf > 0.5:
                        class_name = COCO_CLASSES.get(cls, f"class_{cls}")
                        detected_classes.append(class_name)
                        
                        # Check if it's a blocked class
                        if cls in BLOCKED_CLASSES:
                            blocked_detections.append(f"{class_name} (confidence: {conf:.2f})")
        
        if blocked_detections:
            # Check if it's a person/human
            if any('person' in det.lower() for det in blocked_detections):
                return True, "Image contains human body content. This app supports only educational text images.", detected_classes
            # Other blocked objects
            return True, f"Image contains inappropriate content ({', '.join(blocked_detections[:2])}). This app supports only educational text images.", detected_classes
        
        return False, None, detected_classes
        
    except Exception as e:
        print(f"Object detection error: {e}")
        # On error, be conservative and block
        return True, f"Safety check failed: {str(e)}", []

def detect_faces_and_body_parts(image_path: str) -> Tuple[bool, Optional[str]]:
    """
    Detect faces, hands, and other body parts using OpenCV
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return True, "Could not read image"
        
        # Resize image for faster processing (max 640px on longest side)
        height, width = img.shape[:2]
        max_dim = 640
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Load face cascade
        face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(face_cascade_path):
            face_cascade = cv2.CascadeClassifier(face_cascade_path)
            # Use more strict parameters to reduce false positives
            # scaleFactor=1.2 (less sensitive), minNeighbors=5 (more confident), minSize=(50,50) (larger faces only)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(50, 50))
            
            print(f"📊 Face detection: found {len(faces)} faces")
            
            if len(faces) > 0:
                # Verify it's actually a face by checking size and position
                # Faces should be reasonably sized and not cover the entire image
                for (x, y, w, h) in faces:
                    face_area = w * h
                    image_area = img.shape[0] * img.shape[1]
                    face_ratio = face_area / image_area
                    
                    # Only block if face is reasonably sized (not too small, not covering entire image)
                    if 0.01 < face_ratio < 0.8:  # Face is 1-80% of image
                        print(f"❌ Valid face detected (ratio: {face_ratio:.4f})")
                        return True, "Image contains human body content. This app supports only educational text images."
                
                # Faces detected but seem invalid (too small/large) - might be false positive
                print("⚠️ Face-like patterns detected but seem invalid - allowing image")
        
        # Check for skin tones (simple heuristic - detect large areas of skin-colored pixels)
        # This is a basic check and may have false positives - make it less sensitive
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define skin color range in HSV (narrower range to reduce false positives)
        lower_skin = np.array([5, 30, 80], dtype=np.uint8)  # More restrictive lower bound
        upper_skin = np.array([20, 200, 255], dtype=np.uint8)  # More restrictive upper bound
        
        # Create mask for skin color
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_pixels = cv2.countNonZero(mask)
        total_pixels = img.shape[0] * img.shape[1]
        skin_ratio = skin_pixels / total_pixels
        
        print(f"📊 Skin detection: ratio={skin_ratio:.4f}")
        
        # Much higher threshold - only block if more than 15% is skin-colored
        # This reduces false positives from paper/text colors
        if skin_ratio > 0.15:
            # Also check if it's actually a person by looking for face-like patterns
            # If we detected a face earlier, we already blocked it
            return True, "Image contains human body content. This app supports only educational text images."
        
        # Low skin ratio - likely not a person, allow it
        print("✅ Low skin ratio - allowing image")
        
        return False, None
        
    except Exception as e:
        print(f"Face/body detection error: {e}")
        # On error, be conservative
        return True, f"Safety check failed: {str(e)}"

def detect_text_content(image_path: str) -> Tuple[bool, Optional[str], str]:
    """
    Extract text from image and check for blocked keywords
    Returns: (has_blocked_text, error_message, extracted_text)
    """
    try:
        # Extract text using OCR - optimized for speed
        extracted_text = ""
        try:
            img = Image.open(image_path)
            
            # Resize image for faster OCR (max 1200px on longest side for OCR quality)
            width, height = img.size
            max_dim = 1200
            if max(width, height) > max_dim:
                scale = max_dim / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"📐 Resized image for OCR from {width}x{height} to {new_width}x{new_height}")
            
            # Try OCR with best PSM mode first (PSM 6 is usually best for uniform text blocks)
            try:
                extracted_text = pytesseract.image_to_string(img, config='--psm 6')
                # If we got good text, use it (at least 10 chars)
                if extracted_text and len(extracted_text.strip()) >= 10:
                    print(f"✅ OCR successful with PSM 6 ({len(extracted_text.strip())} chars)")
                else:
                    # Try PSM 11 as fallback (sparse text)
                    text_psm11 = pytesseract.image_to_string(img, config='--psm 11')
                    if text_psm11 and len(text_psm11.strip()) > len(extracted_text.strip()):
                        extracted_text = text_psm11
                        print(f"✅ OCR successful with PSM 11 ({len(extracted_text.strip())} chars)")
            except Exception as ocr_error:
                # If OCR fails, try default mode
                print(f"⚠️ OCR with PSM failed, trying default: {ocr_error}")
                extracted_text = pytesseract.image_to_string(img)
        except Exception as ocr_error:
            # If OCR fails, log but continue
            print(f"⚠️ OCR error (non-blocking): {ocr_error}")
            extracted_text = ""
        
        extracted_text_lower = extracted_text.lower()
        
        # Check for blocked keywords
        found_blocked = []
        for keyword in BLOCKED_KEYWORDS:
            if keyword.lower() in extracted_text_lower:
                found_blocked.append(keyword)
        
        if found_blocked:
            # Check if it's human/body related
            human_keywords = ['nude', 'naked', 'body', 'skin', 'face', 'hand', 'person', 'human']
            if any(kw in ' '.join(found_blocked).lower() for kw in human_keywords):
                return True, "Image contains human body content. This app supports only educational text images.", extracted_text
            # Other blocked content
            return True, f"Image contains inappropriate content. This app supports only educational text images.", extracted_text
        
        # Check if it looks like an ID/certificate (has ID numbers, dates, signatures)
        id_patterns = [
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card pattern
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b[A-Z]{2}\d{7}\b',  # ID number pattern
            r'passport|driver.*license|id card|aadhaar|pan card',
            r'signature|signed by|certified'
        ]
        
        for pattern in id_patterns:
            if re.search(pattern, extracted_text_lower, re.IGNORECASE):
                return True, "Image contains personal identification information (ID, certificate, signature). This app supports only educational text images.", extracted_text
        
        return False, None, extracted_text
        
    except Exception as e:
        print(f"Text detection error: {e}")
        # On error, allow but log
        return False, None, ""

def check_is_study_material(image_path: str, extracted_text: str = "") -> Tuple[bool, Optional[str]]:
    """
    Check if image appears to be study material
    Requires actual text content - blocks random photos without text
    """
    try:
        # PRIMARY CHECK: If we have extracted text with sufficient length, it's study material
        if extracted_text and len(extracted_text.strip()) >= 10:
            # Additional check: ensure it's not just random characters
            # Count alphanumeric characters
            alnum_count = sum(1 for c in extracted_text if c.isalnum())
            if alnum_count >= 5:  # At least 5 alphanumeric characters
                print(f"✅ Text detected ({len(extracted_text.strip())} chars, {alnum_count} alnum) - allowing as study material")
                return True, None
            else:
                print(f"⚠️ Text detected but insufficient alphanumeric content ({alnum_count} chars)")
        
        # SECONDARY CHECK: Analyze image for text-like patterns (optimized for speed)
        img = cv2.imread(image_path)
        if img is None:
            return False, "Could not read image"
        
        # Resize image for faster analysis (max 800px on longest side)
        height, width = img.shape[:2]
        max_dim = 800
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate text density (edges typically indicate text)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = cv2.countNonZero(edges) / (img.shape[0] * img.shape[1])
        
        print(f"📊 Image analysis: edge_density={edge_density:.4f}")
        
        # Check for horizontal lines (typical of text lines)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        detected_lines = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, horizontal_kernel)
        line_density = cv2.countNonZero(detected_lines) / (img.shape[0] * img.shape[1])
        
        print(f"📊 Image analysis: line_density={line_density:.4f}")
        
        # STRICT CHECK: Require significant edge density OR line patterns
        # Edge density > 0.01 (1%) OR line density > 0.005 (0.5%) indicates text
        if edge_density > 0.01 or line_density > 0.005:
            print("✅ Image has text-like patterns (edges/lines) - allowing")
            return True, None
        
        # If edge density is very low, check if it's a photo vs document
        if edge_density < 0.001:
            # Check color variance to see if it's a photo
            color_variance = np.var(img.reshape(-1, 3), axis=0).mean()
            print(f"📊 Image analysis: color_variance={color_variance:.2f}")
            
            # High color variance + low edges = likely a photo, not a document
            if color_variance > 10000 and edge_density < 0.0005:
                return False, "Image does not appear to contain readable text or study materials. Please upload images with clear, readable text content from textbooks, notes, or educational materials."
        
        # If we get here, it's ambiguous - try OCR one more time (optimized for speed)
        try:
            img_pil = Image.open(image_path)
            
            # Resize for faster OCR
            width, height = img_pil.size
            max_dim = 1200
            if max(width, height) > max_dim:
                scale = max_dim / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img_pil = img_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Try only best OCR mode (PSM 6) for speed
            try:
                text = pytesseract.image_to_string(img_pil, config='--psm 6')
                if text and len(text.strip()) >= 10:
                    alnum_count = sum(1 for c in text if c.isalnum())
                    if alnum_count >= 5:
                        print(f"✅ Text found with OCR ({len(text.strip())} chars)")
                        return True, None
            except:
                pass
        except Exception as ocr_error:
            print(f"⚠️ OCR retry failed: {ocr_error}")
        
        # No text found - block the image
        return False, "Image does not contain readable text or study materials. Please upload images with clear, readable text content from textbooks, notes, diagrams, charts, or educational materials."
        
    except Exception as e:
        print(f"Study material check error: {e}")
        # On error, be conservative and require text
        return False, f"Could not verify image contains study material: {str(e)}. Please upload images with clear, readable text content."

def validate_content(image_path: str) -> Tuple[bool, str]:
    """
    Comprehensive content validation
    Returns: (is_valid, error_message)
    STRICT: Blocks inappropriate content AND requires actual text/study material
    Only allows images with readable text content from educational materials
    """
    error_messages = []
    extracted_text = ""
    
    print(f"🔍 Starting content validation for: {image_path}")
    
    # 1. Check for blocked objects (humans, weapons, etc.) - YOLO detection
    try:
        has_blocked_objects, obj_error, detected_classes = detect_blocked_objects(image_path)
        if has_blocked_objects:
            # Only block if it's clearly a person (not other objects)
            if obj_error and "human body" in obj_error.lower():
                error_messages.append(obj_error)
                print(f"❌ Blocked objects detected: {obj_error}")
            else:
                # Other blocked objects - log but don't block (might be false positive)
                print(f"⚠️ Blocked object detected but not human: {obj_error} - allowing")
    except Exception as e:
        print(f"⚠️ Object detection error (non-blocking): {e}")
    
    # 2. Check for faces and body parts - more strict to reduce false positives
    try:
        has_faces, face_error = detect_faces_and_body_parts(image_path)
        if has_faces:
            error_messages.append(face_error)
            print(f"❌ Faces/body parts detected: {face_error}")
        else:
            print("✅ No faces/body parts detected")
    except Exception as e:
        print(f"⚠️ Face detection error (non-blocking): {e}")
    
    # 3. Check text content for blocked keywords and PII
    try:
        has_blocked_text, text_error, extracted_text = detect_text_content(image_path)
        if has_blocked_text:
            error_messages.append(text_error)
            print(f"❌ Blocked text detected: {text_error}")
        else:
            if extracted_text:
                print(f"✅ Clean text extracted ({len(extracted_text.strip())} chars)")
    except Exception as e:
        print(f"⚠️ Text detection error (non-blocking): {e}")
    
    # 4. If we found humans/inappropriate content, block immediately
    if error_messages:
        human_body_errors = [msg for msg in error_messages if "human body" in msg.lower()]
        if human_body_errors:
            print(f"❌ Validation failed: {human_body_errors[0]}")
            return False, human_body_errors[0]
        # Other errors (PII, inappropriate content)
        print(f"❌ Validation failed: {error_messages[0]}")
        return False, error_messages[0]
    
    # 5. Check if image contains study material (text content)
    # This is CRITICAL - we must ensure the image has educational content
    try:
        is_study_material, study_error = check_is_study_material(image_path, extracted_text)
        if not is_study_material:
            error_msg = study_error or "Image does not appear to contain readable text or study materials. Please upload images with clear, readable text content from textbooks, notes, or educational materials."
            print(f"❌ Study material check failed: {error_msg}")
            return False, error_msg
        print("✅ Study material check passed")
    except Exception as e:
        print(f"⚠️ Study material check error: {e}")
        # If check fails, be conservative and require text
        if not extracted_text or len(extracted_text.strip()) < 10:
            return False, "Image does not appear to contain readable text. Please upload images with clear, readable text content from study materials."
    
    # 6. Final verification: Ensure we have sufficient text content (optimized for speed)
    if not extracted_text or len(extracted_text.strip()) < 10:
        # Try OCR one more time (single attempt for speed)
        try:
            img = Image.open(image_path)
            
            # Resize for faster OCR
            width, height = img.size
            max_dim = 1200
            if max(width, height) > max_dim:
                scale = max_dim / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Try only best OCR mode (PSM 6) for speed
            text = pytesseract.image_to_string(img, config='--psm 6')
            if text and len(text.strip()) >= 10:
                # Check for alphanumeric content
                alnum_count = sum(1 for c in text if c.isalnum())
                if alnum_count >= 5:
                    print(f"✅ Text found with final OCR ({len(text.strip())} chars, {alnum_count} alnum)")
                    return True, ""
        except Exception as e:
            print(f"⚠️ Final OCR retry failed: {e}")
        
        # No text found after all attempts
        return False, "Image does not contain readable text. Please upload images with clear, readable text content from textbooks, notes, diagrams, charts, or educational materials."
    
    print("✅ Content validation PASSED - image contains study material")
    return True, ""

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

