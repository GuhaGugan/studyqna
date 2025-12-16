"""
Font Manager for Multilingual PDF Support
Handles Google Noto fonts registration and language detection
"""
import os
import urllib.request
import urllib.error
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from typing import Dict, Tuple, Optional
import re

# Font paths (will be downloaded if not present)
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
os.makedirs(FONT_DIR, exist_ok=True)

# Language to font mapping
LANGUAGE_FONTS = {
    "english": "NotoSans-Regular",
    "spanish": "NotoSans-Regular",
    "tamil": "NotoSansTamil-Regular",
    "hindi": "NotoSansDevanagari-Regular",
    "telugu": "NotoSansTelugu-Regular",
    "kannada": "NotoSansKannada-Regular",
    "malayalam": "NotoSansMalayalam-Regular",
    "arabic": "NotoSansArabic-Regular",
}

# Font file names (Google Noto fonts)
FONT_FILES = {
    "NotoSans-Regular": "NotoSans-Regular.ttf",
    "NotoSansTamil-Regular": "NotoSansTamil-Regular.ttf",
    "NotoSansDevanagari-Regular": "NotoSansDevanagari-Regular.ttf",
    "NotoSansTelugu-Regular": "NotoSansTelugu-Regular.ttf",
    "NotoSansKannada-Regular": "NotoSansKannada-Regular.ttf",
    "NotoSansMalayalam-Regular": "NotoSansMalayalam-Regular.ttf",
    "NotoSansArabic-Regular": "NotoSansArabic-Regular.ttf",
}

# RTL languages
RTL_LANGUAGES = {"arabic"}

# Fallback font (Helvetica for basic Latin)
FALLBACK_FONT = "Helvetica"

# Registered fonts cache
_registered_fonts = {}


def download_font_alternative(font_name: str, font_path: str) -> Optional[str]:
    """
    Alternative font download using jsDelivr CDN
    """
    try:
        alt_urls = {
            "NotoSans-Regular": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosans/NotoSans-Regular.ttf",
            "NotoSansTamil-Regular": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanstamil/NotoSansTamil-Regular.ttf",
            "NotoSansDevanagari-Regular": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansdevanagari/NotoSansDevanagari-Regular.ttf",
            "NotoSansTelugu-Regular": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanstelugu/NotoSansTelugu-Regular.ttf",
            "NotoSansKannada-Regular": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanskannada/NotoSansKannada-Regular.ttf",
            "NotoSansMalayalam-Regular": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansmalayalam/NotoSansMalayalam-Regular.ttf",
            "NotoSansArabic-Regular": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansarabic/NotoSansArabic-Regular.ttf",
        }
        
        url = alt_urls.get(font_name)
        if url:
            print(f"📥 Trying alternative source (jsDelivr) for {font_name}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(font_path, 'wb') as f:
                    f.write(response.read())
                print(f"✅ Font downloaded from alternative source: {font_name}")
                return font_path
    except Exception as e:
        print(f"❌ Alternative download failed for {font_name}: {e}")
    
    return None


def download_font(font_name: str) -> Optional[str]:
    """
    Download Google Noto font if not present
    Returns path to font file or None if download fails
    """
    font_file = FONT_FILES.get(font_name)
    if not font_file:
        return None
    
    font_path = os.path.join(FONT_DIR, font_file)
    
    # If font already exists, return path
    if os.path.exists(font_path):
        return font_path
    
    # Google Fonts URLs - using mixed sources (google/fonts for NotoSans, googlefonts/noto-fonts for others)
    FONT_URLS = {
        "NotoSans-Regular": "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf",
        "NotoSansTamil-Regular": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf",
        "NotoSansDevanagari-Regular": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf",
        "NotoSansTelugu-Regular": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Regular.ttf",
        "NotoSansKannada-Regular": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf",
        "NotoSansMalayalam-Regular": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansMalayalam/NotoSansMalayalam-Regular.ttf",
        "NotoSansArabic-Regular": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf",
    }
    
    url = FONT_URLS.get(font_name)
    if not url:
        print(f"⚠️  No URL found for font: {font_name}")
        return None
    
    try:
        print(f"📥 Downloading font: {font_name}...")
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status == 200:
                with open(font_path, 'wb') as f:
                    f.write(response.read())
                file_size = os.path.getsize(font_path)
                print(f"✅ Font downloaded successfully: {font_name} ({file_size:,} bytes)")
                return font_path
            else:
                print(f"❌ HTTP {response.status} downloading {font_name}")
                return None
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code} downloading {font_name}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"❌ URL Error downloading {font_name}: {e.reason}")
        return None
    except Exception as e:
        print(f"❌ Failed to download font {font_name}: {e}")
        return None


def register_font(font_name: str) -> bool:
    """
    Register a font with ReportLab
    Returns True if successful, False otherwise
    """
    if font_name in _registered_fonts:
        return True  # Already registered
    
    # Try to get font path
    font_path = os.path.join(FONT_DIR, FONT_FILES.get(font_name, ""))
    
    # Download if not exists
    if not os.path.exists(font_path):
        font_path = download_font(font_name)
        if not font_path:
            print(f"⚠️  Font {font_name} not available, will use fallback")
            return False
    
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        _registered_fonts[font_name] = font_path
        print(f"✅ Registered font: {font_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to register font {font_name}: {e}")
        return False


def detect_language(text: str, default_language: str = "english") -> str:
    """
    Detect language from text content
    Returns language code
    """
    if not text or not text.strip():
        return default_language
    
    text_sample = text[:500]  # Sample first 500 chars
    
    # Tamil: U+0B80–U+0BFF
    if re.search(r'[\u0B80-\u0BFF]', text_sample):
        return "tamil"
    
    # Hindi/Devanagari: U+0900–U+097F
    if re.search(r'[\u0900-\u097F]', text_sample):
        return "hindi"
    
    # Telugu: U+0C00–U+0C7F
    if re.search(r'[\u0C00-\u0C7F]', text_sample):
        return "telugu"
    
    # Kannada: U+0C80–U+0CFF
    if re.search(r'[\u0C80-\u0CFF]', text_sample):
        return "kannada"
    
    # Malayalam: U+0D00–U+0D7F
    if re.search(r'[\u0D00-\u0D7F]', text_sample):
        return "malayalam"
    
    # Arabic: U+0600–U+06FF
    if re.search(r'[\u0600-\u06FF]', text_sample):
        return "arabic"
    
    # Spanish: Check for common Spanish characters/words
    spanish_indicators = ['ñ', 'Ñ', '¿', '¡', 'á', 'é', 'í', 'ó', 'ú', 'Á', 'É', 'Í', 'Ó', 'Ú']
    if any(char in text_sample for char in spanish_indicators):
        return "spanish"
    
    # Default to English
    return default_language


def get_font_for_language(language: str) -> str:
    """
    Get font name for a given language
    Returns font name or fallback
    """
    language = language.lower().strip()
    font_name = LANGUAGE_FONTS.get(language, LANGUAGE_FONTS["english"])
    
    # Register font if not already registered
    if font_name not in _registered_fonts:
        register_font(font_name)
    
    # Return font if registered, otherwise fallback
    if font_name in _registered_fonts:
        return font_name
    return FALLBACK_FONT


def is_rtl(language: str) -> bool:
    """
    Check if language is Right-to-Left
    """
    return language.lower().strip() in RTL_LANGUAGES


def get_alignment(language: str, default_alignment: int = TA_LEFT) -> int:
    """
    Get text alignment for language (RTL for Arabic, LTR for others)
    """
    if is_rtl(language):
        return TA_RIGHT
    return default_alignment


def initialize_fonts():
    """
    Initialize and register all fonts on startup
    Note: Fonts will be downloaded on-demand when needed
    """
    print("🔤 Font system initialized (fonts will be downloaded on-demand)")
    # Don't download all fonts on startup - download them when needed
    # This prevents long startup times and 404 errors if fonts aren't available
