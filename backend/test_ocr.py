#!/usr/bin/env python3
"""
Test script to verify OCR functionality for image-based PDFs
Run this on your production server to diagnose OCR issues
"""

import sys
import os

def test_pdf2image():
    """Test if pdf2image can convert PDFs"""
    try:
        from pdf2image import convert_from_bytes
        print("✅ pdf2image is installed")
        
        # Test with a minimal PDF
        test_pdf = b'''%PDF-1.4
1 0 obj
<< /Type /Catalog >>
endobj
xref
0 0
trailer
<< /Size 0 /Root 1 0 R >>
startxref
0
%%EOF'''
        
        try:
            images = convert_from_bytes(test_pdf, dpi=100)
            print(f"✅ Poppler is working! Converted {len(images)} page(s)")
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if "poppler" in error_msg or "pdftoppm" in error_msg or "cannot find" in error_msg:
                print(f"❌ Poppler utilities not found: {e}")
                print("\nPlease install poppler:")
                print("  Ubuntu/Debian: sudo apt-get install poppler-utils")
                print("  CentOS/RHEL: sudo yum install poppler-utils")
                print("  Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases")
                return False
            else:
                print(f"⚠️ PDF conversion error: {e}")
                return False
    except ImportError:
        print("❌ pdf2image is not installed")
        print("Install with: pip install pdf2image")
        return False

def test_pytesseract():
    """Test if pytesseract is working"""
    try:
        import pytesseract
        from PIL import Image
        import numpy as np
        
        print("✅ pytesseract is installed")
        
        # Create a simple test image with text
        img = Image.new('RGB', (200, 50), color='white')
        # Note: This is just a basic test - actual OCR needs real text images
        
        try:
            # Test if tesseract command is available
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract is available (version: {version})")
            return True
        except Exception as e:
            print(f"❌ Tesseract not found: {e}")
            print("\nPlease install tesseract:")
            print("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
            print("  CentOS/RHEL: sudo yum install tesseract")
            print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
            return False
    except ImportError:
        print("❌ pytesseract is not installed")
        print("Install with: pip install pytesseract")
        return False

def test_opencv():
    """Test if OpenCV is available"""
    try:
        import cv2
        print(f"✅ OpenCV is installed (version: {cv2.__version__})")
        return True
    except ImportError:
        print("❌ OpenCV is not installed")
        print("Install with: pip install opencv-python")
        return False

def main():
    print("=" * 60)
    print("OCR Functionality Test")
    print("=" * 60)
    print()
    
    results = []
    
    print("1. Testing pdf2image and poppler...")
    results.append(("pdf2image + poppler", test_pdf2image()))
    print()
    
    print("2. Testing pytesseract...")
    results.append(("pytesseract", test_pytesseract()))
    print()
    
    print("3. Testing OpenCV...")
    results.append(("OpenCV", test_opencv()))
    print()
    
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ All OCR dependencies are properly installed!")
        print("Image-based PDF processing should work correctly.")
    else:
        print("❌ Some dependencies are missing or not configured correctly.")
        print("Please install the missing components as shown above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

