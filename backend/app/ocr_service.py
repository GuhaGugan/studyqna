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
    Extract text from PDF
    """
    try:
        from PyPDF2 import PdfReader
        from app.storage_service import read_file
        import io
        
        pdf_data = read_file(pdf_path)
        pdf_reader = PdfReader(io.BytesIO(pdf_data))
        
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        combined = "\n\n".join(text_parts) if text_parts else ""

        # If mathpix is available and the PDF seems scanned/low-text, try mathpix PDF OCR
        if (not combined or len(combined.strip()) < 100) and _mathpix_available():
            pdf_text = _mathpix_ocr_pdf(pdf_data)
            if pdf_text:
                return pdf_text.strip()
        
        return combined if combined else None
        
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

