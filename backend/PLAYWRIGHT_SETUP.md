# Playwright Setup Guide

Playwright uses Chromium for PDF generation, providing **pixel-perfect rendering** that matches your web interface exactly.

## Installation

1. **Install Playwright Python package:**
   ```bash
   cd backend
   pip install playwright==1.40.0
   ```

2. **Install Chromium browser (required once):**
   ```bash
   playwright install chromium
   ```
   
   This downloads Chromium (~170MB) automatically. It only needs to be done once.

## Why Playwright?

- ✅ **Pixel-perfect rendering** - Uses real Chromium browser
- ✅ **Perfect Unicode support** - Excellent Indic script rendering (Tamil, Hindi, etc.)
- ✅ **No external binaries** - Downloads Chromium automatically
- ✅ **Matches web interface** - Same rendering engine as browsers
- ✅ **Better font rendering** - Handles custom fonts perfectly

## Testing

After installation, test PDF generation:

```bash
python test_pdf_generation.py
```

The PDF should now render **exactly** like your web interface with perfect Tamil text rendering.

## Fallback Order

The system tries PDF generators in this order:
1. **Playwright** (best quality) - if installed
2. **pdfkit/wkhtmltopdf** - if installed
3. **ReportLab** (fallback) - always available

## Troubleshooting

If you see "playwright not installed":
- Run: `pip install playwright==1.40.0`
- Then: `playwright install chromium`

If Chromium download fails:
- Check internet connection
- Try: `playwright install chromium --with-deps` (Linux)


