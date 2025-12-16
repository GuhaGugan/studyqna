# Content Filtering System

## 🚫 BLOCKED Content Categories

The system automatically blocks the following content:

### 1. Human Bodies & Body Parts
- Full or partial human bodies
- Faces, hands, skin, limbs, eyes
- Any visible human body parts
- **Detection Methods:**
  - YOLO object detection (person class)
  - OpenCV face detection (Haar cascades)
  - Skin tone detection (HSV color analysis)

### 2. Nudity & Sexual Content
- Nudity, sexual content, sexualized imagery
- **Detection Methods:**
  - Keyword detection in OCR text
  - Visual pattern analysis

### 3. Violence & Weapons
- Violence, blood, injuries, weapons
- Knives, guns, and other weapons
- **Detection Methods:**
  - YOLO object detection (weapon classes)
  - Keyword detection in OCR text

### 4. Graphic/Disturbing Content
- Graphic or disturbing imagery
- **Detection Methods:**
  - Visual pattern analysis
  - Content classification

### 5. Medical/Anatomical Content
- Medical body parts
- Anatomical diagrams
- X-rays, CT scans, MRIs
- **Detection Methods:**
  - Keyword detection in OCR text
  - Visual pattern recognition

### 6. Personal Information (PII)
- IDs, certificates, signatures
- Passports, driver licenses
- Credit cards, bank information
- Social security numbers
- **Detection Methods:**
  - OCR text extraction
  - Pattern matching (ID numbers, dates)
  - Keyword detection

## ✅ ALLOWED Content Categories

The system only allows:

### 1. Textbook Pages
- Printed textbook pages
- Study book content
- Educational material

### 2. Printed Study Materials
- Handwritten notes (clean text)
- Printed study sheets
- Lecture notes

### 3. Diagrams, Charts, Tables, Graphs
- Scientific diagrams
- Mathematical charts
- Data tables
- Graphs and illustrations

### 4. Clean Text from Notebooks
- Handwritten study notes
- Printed sheets with text
- Document pages

## 🔍 Detection Methods

### 1. Object Detection (YOLO)
- Detects: persons, weapons, objects
- Model: YOLOv8n (nano - fast inference)
- Confidence threshold: 0.5

### 2. Face Detection (OpenCV)
- Uses Haar cascades
- Detects frontal faces
- Blocks any face detection

### 3. Skin Tone Detection
- HSV color space analysis
- Detects large areas of skin-colored pixels
- Threshold: >5% of image

### 4. OCR Text Analysis (Tesseract)
- Extracts text from images
- Checks for blocked keywords
- Detects ID patterns (SSN, credit cards, etc.)
- Identifies study-related keywords

### 5. Image Quality Analysis
- Edge detection (text density)
- Color variance analysis
- Blur detection (Laplacian variance)

## 📋 Validation Process

When an image is uploaded:

1. **Object Detection**
   - Scans for persons, weapons, blocked objects
   - If detected → **BLOCKED**

2. **Face/Body Part Detection**
   - Checks for faces using Haar cascades
   - Analyzes skin tone areas
   - If detected → **BLOCKED**

3. **Text Content Analysis**
   - Extracts text using OCR
   - Checks for blocked keywords
   - Looks for ID/certificate patterns
   - If detected → **BLOCKED**

4. **Study Material Verification**
   - Checks for study-related keywords
   - Analyzes image characteristics:
     - Text density (edge detection)
     - Color variance
     - Layout structure
   - If not study material → **BLOCKED**

5. **Quality Check**
   - Verifies image is readable
   - Checks for blur
   - If too blurry → **BLOCKED**

## 🛡️ Security Features

1. **Conservative Approach**
   - On detection errors, blocks by default
   - Better safe than sorry

2. **Multiple Detection Layers**
   - Object detection
   - Face detection
   - Text analysis
   - Visual analysis

3. **Real-time Validation**
   - Validates before saving
   - Immediate feedback to user

4. **Privacy Protection**
   - Blocks PII automatically
   - Prevents data leaks

## ⚙️ Configuration

### Blocked Keywords List
Located in `backend/app/content_validation.py`:
```python
BLOCKED_KEYWORDS = [
    # Violence/Weapons
    'gun', 'pistol', 'rifle', 'weapon', 'knife', ...
    # Sexual content
    'nude', 'naked', 'sex', 'sexual', ...
    # Medical/Anatomical
    'anatomy', 'skeleton', 'bone', 'organ', ...
    # PII/IDs
    'passport', 'id card', 'driver license', ...
]
```

### Allowed Keywords List
```python
ALLOWED_KEYWORDS = [
    'textbook', 'book', 'page', 'chapter', ...
    'diagram', 'chart', 'graph', 'table', ...
    'formula', 'equation', 'problem', ...
]
```

### Detection Thresholds
- **YOLO Confidence**: 0.5 (50%)
- **Skin Ratio**: 0.05 (5% of image)
- **Edge Density**: 0.05 (5% of pixels)
- **Color Variance**: 5000 (for photo vs document)

## 🐛 Troubleshooting

### False Positives
If legitimate study material is blocked:
1. Check image quality (not too blurry)
2. Ensure text is clear and readable
3. Avoid any human elements in frame
4. Make sure it's clearly study material

### False Negatives
If inappropriate content gets through:
1. System uses multiple detection methods
2. Report any issues immediately
3. System is continuously improved

### Performance
- YOLO model loads on first use (cached)
- OCR may take 1-3 seconds
- Total validation: ~2-5 seconds per image

## 📝 Notes

- **Model Requirements**: YOLOv8n model downloads automatically on first use
- **OCR Dependency**: Requires Tesseract OCR installed on system
- **OpenCV**: Requires OpenCV with Haar cascade files
- **Error Handling**: Conservative approach - blocks on errors

## 🔄 Updates

The content filtering system is continuously improved:
- New blocked keywords added
- Detection methods refined
- False positive/negative rates optimized
- Performance improvements


