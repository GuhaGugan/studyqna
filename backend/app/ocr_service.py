import pytesseract
from PIL import Image
import cv2
import numpy as np
from typing import Optional
from app.storage_service import read_file
import io
import base64
import os
import time
import requests

def extract_text_from_image(image_path: str) -> Optional[str]:
    """
    Extract text from image using OCR
    """
    try:
        # Read image
        image_data = read_file(image_path)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Preprocess image for better OCR
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(thresh)
        
        # Extract text (baseline)
        text = pytesseract.image_to_string(processed_image, lang='eng')
        text = text.strip() if text else ""

        # If mathpix is available and the baseline is weak, try mathpix for better math OCR
        if len(text) < 50 and _mathpix_available():
            mathpix_text = _mathpix_ocr_image(processed_image)
            if mathpix_text:
                return mathpix_text.strip()

        return text if text else None
        
    except Exception as e:
        print(f"OCR error: {e}")
        return None

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text from PDF (handles both text-based and image-based/scanned PDFs)
    """
    try:
        from PyPDF2 import PdfReader
        from app.storage_service import read_file
        import io
        
        pdf_data = read_file(pdf_path)
        pdf_reader = PdfReader(io.BytesIO(pdf_data))
        
        # First, try to extract text directly (for text-based PDFs)
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        combined = "\n\n".join(text_parts) if text_parts else ""
        
        # Check if we got sufficient text (at least 50 characters per page on average)
        num_pages = len(pdf_reader.pages)
        min_expected_text = max(50, num_pages * 50)  # At least 50 chars per page
        
        # If we have good text extraction, return it
        if combined and len(combined.strip()) >= min_expected_text:
            print(f"✅ PDF text extraction successful: {len(combined.strip())} characters from {num_pages} pages")
            return combined.strip()
        
        # If text extraction is weak or empty, it's likely an image-based PDF
        # Use OCR on PDF pages converted to images
        print(f"⚠️ PDF appears to be image-based (extracted only {len(combined.strip()) if combined else 0} chars). Using OCR...")
        
        try:
            from pdf2image import convert_from_bytes
            import tempfile
            import os
            
            # Convert PDF pages to images
            try:
                images = convert_from_bytes(pdf_data, dpi=300)  # Higher DPI for better OCR quality
                print(f"📄 Converted {len(images)} PDF pages to images for OCR")
            except Exception as convert_error:
                # Check if it's a poppler error
                error_str = str(convert_error).lower()
                if "poppler" in error_str or "pdftoppm" in error_str or "cannot find" in error_str:
                    raise Exception(f"Poppler utilities not found or not in PATH. Please install poppler: On Windows: choco install poppler (or download from poppler website), On Linux: sudo apt-get install poppler-utils, On macOS: brew install poppler. Original error: {convert_error}")
                else:
                    raise Exception(f"Failed to convert PDF to images: {convert_error}")
            
            # Check if Tesseract is available before processing
            try:
                pytesseract.get_tesseract_version()
            except Exception as tesseract_check_error:
                error_str = str(tesseract_check_error).lower()
                if "tesseract" in error_str and ("not found" in error_str or "not installed" in error_str):
                    raise Exception(f"Tesseract OCR is not installed or not in PATH. Please install tesseract: On Ubuntu/Debian: sudo apt-get install tesseract-ocr, On CentOS/RHEL: sudo yum install tesseract, On Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki. Original error: {tesseract_check_error}")
                else:
                    raise Exception(f"Tesseract check failed: {tesseract_check_error}")
            
            ocr_text_parts = []
            tesseract_error_occurred = False
            failed_pages = []
            for i, image in enumerate(images):
                try:
                    print(f"📄 Processing page {i+1}/{len(images)} for OCR...")
                    # Preprocess image for better OCR
                    img_array = np.array(image)
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                    
                    # Apply thresholding
                    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    # Convert back to PIL Image
                    processed_image = Image.fromarray(thresh)
                    
                    # Extract text using OCR
                    page_text = pytesseract.image_to_string(processed_image, lang='eng', config='--psm 6')
                    if page_text and page_text.strip():
                        ocr_text_parts.append(page_text.strip())
                        print(f"✅ OCR extracted {len(page_text.strip())} characters from page {i+1}")
                    else:
                        print(f"⚠️ OCR returned empty text for page {i+1} (image may be blank or unreadable)")
                        failed_pages.append(i+1)
                except pytesseract.TesseractNotFoundError as tesseract_error:
                    tesseract_error_occurred = True
                    error_msg = f"Tesseract OCR is not installed or not in PATH. Please install tesseract: On Ubuntu/Debian: sudo apt-get install tesseract-ocr, On CentOS/RHEL: sudo yum install tesseract, On Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki. Original error: {tesseract_error}"
                    print(f"❌ {error_msg}")
                    raise Exception(error_msg)
                except Exception as page_error:
                    error_str = str(page_error).lower()
                    if "tesseract" in error_str and ("not found" in error_str or "not installed" in error_str):
                        tesseract_error_occurred = True
                        error_msg = f"Tesseract OCR is not installed or not in PATH. Please install tesseract: On Ubuntu/Debian: sudo apt-get install tesseract-ocr, On CentOS/RHEL: sudo yum install tesseract, On Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki. Original error: {page_error}"
                        print(f"❌ {error_msg}")
                        raise Exception(error_msg)
                    else:
                        print(f"⚠️ OCR error on page {i+1}: {page_error}")
                        failed_pages.append(i+1)
                        continue
            
            if ocr_text_parts:
                ocr_combined = "\n\n".join(ocr_text_parts)
                print(f"✅ OCR extraction successful: {len(ocr_combined)} total characters from {len(ocr_text_parts)} pages")
                if failed_pages:
                    print(f"⚠️ Note: {len(failed_pages)} page(s) failed OCR: {failed_pages}")
                return ocr_combined.strip()
            else:
                if tesseract_error_occurred:
                    raise Exception("Tesseract OCR failed. Please ensure Tesseract is installed and in PATH.")
                else:
                    failed_info = f" Failed pages: {failed_pages}" if failed_pages else ""
                    error_msg = f"OCR failed to extract text from any of the {len(images)} page(s).{failed_info} This could indicate: 1) Very low-quality or corrupted images, 2) Images with no readable text, 3) OCR processing errors. Please check the PDF quality and ensure images contain readable text."
                    print(f"⚠️ {error_msg}")
                    # Raise exception instead of returning None to provide better error message
                    raise Exception(error_msg)
        except ImportError as import_err:
            error_msg = f"pdf2image not available: {import_err}"
            print(f"⚠️ {error_msg}")
            print("⚠️ Install with: pip install pdf2image")
            print("⚠️ Also install poppler: On Windows: choco install poppler, On Linux: sudo apt-get install poppler-utils")
            # Re-raise with more context for better error handling
            raise Exception(f"OCR dependencies missing: {error_msg}. Please install pdf2image and poppler utilities.")
        except Exception as ocr_error:
            error_msg = f"PDF OCR error: {ocr_error}"
            print(f"⚠️ {error_msg}")
            # Check if it's a poppler error
            if "poppler" in str(ocr_error).lower() or "pdftoppm" in str(ocr_error).lower():
                raise Exception(f"Poppler utilities not found. Please install poppler: On Windows: choco install poppler, On Linux: sudo apt-get install poppler-utils. Original error: {ocr_error}")
            raise Exception(f"OCR processing failed: {ocr_error}")
        
        # If OCR fails, try Mathpix as fallback (if available)
        if (not combined or len(combined.strip()) < 100) and _mathpix_available():
            print("🔄 Trying Mathpix PDF OCR as fallback...")
            pdf_text = _mathpix_ocr_pdf(pdf_data)
            if pdf_text:
                print(f"✅ Mathpix OCR successful: {len(pdf_text.strip())} characters")
                return pdf_text.strip()
        
        # Return whatever text we got (even if minimal)
        return combined.strip() if combined else None
        
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return None

# ----------------------------
# Mathpix helpers (optional)
# ----------------------------

def _mathpix_available() -> bool:
    return bool(os.getenv("MATHPIX_APP_ID") and os.getenv("MATHPIX_APP_KEY"))


def _mathpix_headers():
    return {
        "app_id": os.getenv("MATHPIX_APP_ID", ""),
        "app_key": os.getenv("MATHPIX_APP_KEY", ""),
        "Content-type": "application/json"
    }


def _mathpix_ocr_image(pil_image: Image.Image) -> Optional[str]:
    try:
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        payload = {
            "src": f"data:image/png;base64,{img_str}",
            "formats": ["text"],
            "data_options": {
                "include_asciimath": True,
                "include_latex": True,
                "include_mathml": True
            }
        }
        r = requests.post("https://api.mathpix.com/v3/text", json=payload, headers=_mathpix_headers(), timeout=30)
        if r.status_code == 200:
            data = r.json()
            # Prefer LaTeX if available, else text
            latex = data.get("latex_styled") or data.get("latex") or ""
            plain = data.get("text") or ""
            return latex or plain
        else:
            print(f"Mathpix image OCR failed: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Mathpix image OCR error: {e}")
    return None


def _mathpix_ocr_pdf(pdf_bytes: bytes) -> Optional[str]:
    """
    Use Mathpix PDF OCR (asynchronous) to extract math-aware text.
    This is optional and only used when baseline PDF text is weak.
    """
    try:
        # Submit PDF
        submit_resp = requests.post(
            "https://api.mathpix.com/v3/pdf",
            files={"file": ("document.pdf", pdf_bytes, "application/pdf")},
            data={"options_json": '{"math_inline_delimiters":["$", "$"],"rm_spaces":true}'},
            headers=_mathpix_headers(),
            timeout=60
        )
        if submit_resp.status_code not in (200, 202):
            print(f"Mathpix PDF submit failed: {submit_resp.status_code} {submit_resp.text}")
            return None
        submit_data = submit_resp.json()
        request_id = submit_data.get("pdf_id") or submit_data.get("request_id")
        if not request_id:
            print("Mathpix PDF submit failed: no request_id")
            return None
        
        # Poll for completion
        for _ in range(20):  # up to ~20 * 3s = 60s
            time.sleep(3)
            status_resp = requests.get(
                f"https://api.mathpix.com/v3/pdf/{request_id}",
                headers=_mathpix_headers(),
                timeout=30
            )
            if status_resp.status_code != 200:
                continue
            status_data = status_resp.json()
            status = status_data.get("status")
            if status == "completed":
                # Get text output
                text_url = status_data.get("text") or status_data.get("text_url")
                if text_url:
                    text_resp = requests.get(text_url, timeout=30)
                    if text_resp.status_code == 200:
                        return text_resp.text
                # If inline text present
                pages = status_data.get("pages")
                if pages and isinstance(pages, list):
                    return "\n\n".join(p.get("text", "") for p in pages if p.get("text"))
                return None
            if status in ("error", "failed"):
                print(f"Mathpix PDF OCR error status: {status}")
                return None
        print("Mathpix PDF OCR timed out")
        return None
    except Exception as e:
        print(f"Mathpix PDF OCR exception: {e}")
        return None

