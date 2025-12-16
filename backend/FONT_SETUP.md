# Font Setup Guide for Multilingual PDF Support

## Overview
The StudyQnA Generator now supports multilingual PDF generation with Google Noto fonts for:
- English, Spanish
- Tamil (தமிழ்)
- Hindi (हिंदी)
- Telugu (తెలుగు)
- Kannada (ಕನ್ನಡ)
- Malayalam (മലയാളം)
- Arabic (العربية) - with RTL support

## Automatic Font Download
Fonts are automatically downloaded from Google Fonts CDN on first use. They are stored in:
```
backend/app/fonts/
```

## Manual Font Installation (Optional)
If automatic download fails, you can manually download fonts:

1. **Download Google Noto Fonts:**
   - Visit: https://fonts.google.com/noto
   - Download the following fonts:
     - Noto Sans (for English/Spanish)
     - Noto Sans Tamil
     - Noto Sans Devanagari (for Hindi)
     - Noto Sans Telugu
     - Noto Sans Kannada
     - Noto Sans Malayalam
     - Noto Sans Arabic

2. **Extract and Place Fonts:**
   - Extract the `.ttf` files
   - Place them in `backend/app/fonts/` directory
   - Rename them to match:
     - `NotoSans-Regular.ttf`
     - `NotoSansTamil-Regular.ttf`
     - `NotoSansDevanagari-Regular.ttf`
     - `NotoSansTelugu-Regular.ttf`
     - `NotoSansKannada-Regular.ttf`
     - `NotoSansMalayalam-Regular.ttf`
     - `NotoSansArabic-Regular.ttf`

## Font Directory Structure
```
backend/
  app/
    fonts/
      NotoSans-Regular.ttf
      NotoSansTamil-Regular.ttf
      NotoSansDevanagari-Regular.ttf
      NotoSansTelugu-Regular.ttf
      NotoSansKannada-Regular.ttf
      NotoSansMalayalam-Regular.ttf
      NotoSansArabic-Regular.ttf
```

## Features
- ✅ Automatic language detection from content
- ✅ Automatic font selection based on language
- ✅ RTL (Right-to-Left) support for Arabic
- ✅ Proper glyph rendering (no square blocks)
- ✅ Modern PDF layout with blue headers (#003366)
- ✅ Title: 22pt, Body: 12pt
- ✅ Bordered question boxes
- ✅ Green answer boxes

## Troubleshooting

### Fonts Not Downloading
- Check internet connection
- Verify write permissions for `backend/app/fonts/` directory
- Check server logs for download errors

### Missing Glyphs (Square Blocks)
- Ensure fonts are properly downloaded
- Verify font files are not corrupted
- Check that correct font is selected for language

### RTL Not Working
- Verify Arabic language is detected correctly
- Check that NotoSansArabic-Regular.ttf is present
- Ensure ReportLab version supports RTL

## Testing
To test multilingual support:
1. Generate Q&A in different languages
2. Download as PDF
3. Verify correct font is used
4. For Arabic, verify RTL rendering


