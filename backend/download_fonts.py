"""
Manual Font Download Script
Downloads Google Noto fonts for multilingual PDF support
Run this script to download fonts manually if automatic download fails
"""
import os
import urllib.request
import urllib.error

FONT_DIR = os.path.join(os.path.dirname(__file__), "app", "fonts")
os.makedirs(FONT_DIR, exist_ok=True)

# Font URLs - using mixed sources (google/fonts for NotoSans, googlefonts/noto-fonts for others)
FONT_DOWNLOADS = {
    "NotoSans-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf",
    "NotoSansTamil-Regular.ttf": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf",
    "NotoSansDevanagari-Regular.ttf": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf",
    "NotoSansTelugu-Regular.ttf": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Regular.ttf",
    "NotoSansKannada-Regular.ttf": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf",
    "NotoSansMalayalam-Regular.ttf": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansMalayalam/NotoSansMalayalam-Regular.ttf",
    "NotoSansArabic-Regular.ttf": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf",
}

def download_font(font_file: str) -> bool:
    """Download a single font file"""
    font_path = os.path.join(FONT_DIR, font_file)
    
    # Skip if already exists
    if os.path.exists(font_path):
        print(f"✅ {font_file} already exists")
        return True
    
    url = FONT_DOWNLOADS.get(font_file)
    if not url:
        print(f"❌ No URL found for {font_file}")
        return False
    
    try:
        print(f"📥 Downloading {font_file}...")
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status == 200:
                with open(font_path, 'wb') as f:
                    f.write(response.read())
                file_size = os.path.getsize(font_path)
                print(f"✅ Downloaded {font_file} ({file_size:,} bytes)")
                return True
            else:
                print(f"❌ HTTP {response.status} downloading {font_file}")
                return False
    except Exception as e:
        print(f"❌ Failed to download {font_file}: {e}")
        return False

if __name__ == "__main__":
    print("🔤 Downloading Google Noto Fonts for Multilingual PDF Support\n")
    print(f"Font directory: {FONT_DIR}\n")
    
    success_count = 0
    total_count = len(FONT_DOWNLOADS)
    
    for font_file in FONT_DOWNLOADS.keys():
        if download_font(font_file):
            success_count += 1
        print()
    
    print(f"\n{'='*60}")
    print(f"Download complete: {success_count}/{total_count} fonts")
    if success_count == total_count:
        print("✅ All fonts downloaded successfully!")
    else:
        print(f"⚠️  {total_count - success_count} fonts failed to download")
        print("You can manually download fonts from:")
        print("https://fonts.google.com/noto")
    print(f"{'='*60}")

