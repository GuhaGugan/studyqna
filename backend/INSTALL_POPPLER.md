# Installing OCR Dependencies for Image-Based PDF Processing

## Required Dependencies

For image-based/scanned PDF processing, you need **two** components:

1. **Poppler Utilities**: Converts PDF pages to images
2. **Tesseract OCR**: Extracts text from images

## Why These Are Required

- **Poppler**: Required for converting PDF pages to images, which is necessary for OCR processing of image-based/scanned PDFs.
- **Tesseract**: Required for performing OCR (Optical Character Recognition) on the converted images to extract text.

## Installation Instructions

### Ubuntu/Debian (Lightsail/EC2)
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr
```

### Verify Installation
```bash
# Verify Poppler
pdftoppm -v
# Should output version information

# Verify Tesseract
tesseract --version
# Should output version information
```

### CentOS/RHEL
```bash
sudo yum install poppler-utils tesseract
# or for newer versions:
sudo dnf install poppler-utils tesseract
```

### Windows Server
1. **Install Poppler:**
   - Download from: https://github.com/oschwartz10612/poppler-windows/releases
   - Extract to a folder (e.g., `C:\poppler`)
   - Add to PATH or set environment variable:
     ```powershell
     $env:PATH += ";C:\poppler\Library\bin"
     ```

2. **Install Tesseract:**
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Run the installer
   - Default location: `C:\Program Files\Tesseract-OCR`
   - During installation, check "Add to PATH"

### macOS
```bash
brew install poppler tesseract
```

## Testing OCR Functionality

After installation, test with:
```bash
# Test Poppler
python -c "from pdf2image import convert_from_bytes; print('Poppler is working!')"

# Test Tesseract
python -c "import pytesseract; print(f'Tesseract version: {pytesseract.get_tesseract_version()}')"

# Or use the provided test script
python backend/test_ocr.py
```

## Troubleshooting

If you still get errors after installing dependencies:

1. **Check if poppler is in PATH:**
   ```bash
   which pdftoppm  # Linux/Mac
   where pdftoppm  # Windows
   ```

2. **Check if tesseract is in PATH:**
   ```bash
   which tesseract  # Linux/Mac
   where tesseract  # Windows
   ```

2. **If not in PATH, specify path in code:**
   You may need to set the poppler path in your environment or code:
   ```python
   from pdf2image import convert_from_bytes
   import os
   os.environ['PATH'] += ':/usr/bin'  # Add poppler path if needed
   ```

3. **Check server logs** for detailed OCR error messages

4. **Verify PDF is not corrupted:**
   - Try opening the PDF in a PDF viewer
   - Check if it's actually an image-based PDF (scanned document)

## Production Server Setup (Lightsail)

For AWS Lightsail Ubuntu instance:

```bash
# SSH into your Lightsail instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update package list
sudo apt-get update

# Install both dependencies
sudo apt-get install -y poppler-utils tesseract-ocr

# Verify installation
pdftoppm -v
tesseract --version

# Restart your application
# (depends on how you're running it - systemd, docker, etc.)
sudo systemctl restart your-app-service
# or if using docker:
docker-compose restart
```

## Docker Setup

If using Docker, add to your Dockerfile:

```dockerfile
# For Ubuntu-based image
RUN apt-get update && apt-get install -y poppler-utils tesseract-ocr && rm -rf /var/lib/apt/lists/*

# For Alpine-based image
RUN apk add --no-cache poppler-utils tesseract-ocr
```

