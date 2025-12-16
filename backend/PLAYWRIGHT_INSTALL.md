# Installing Playwright for PDF Generation

Playwright provides the **best PDF rendering quality** (pixel-perfect, matches web interface exactly).

## Installation Steps

### Option 1: Install Visual C++ Build Tools (Recommended)

1. **Download Visual C++ Build Tools:**
   - Go to: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Download "Build Tools for Visual Studio 2022"

2. **Install:**
   - Run the installer
   - Select "Desktop development with C++" workload
   - Click Install (this will take ~3-6 GB)

3. **Install Playwright:**
   ```bash
   cd backend
   pip install playwright==1.48.0
   playwright install chromium
   ```

### Option 2: Try Pre-built Wheel (Faster, but may not work)

```bash
cd backend
# Try to install greenlet from pre-built wheel
pip install --only-binary :all: greenlet
pip install playwright==1.48.0
playwright install chromium
```

### Option 3: Use Alternative (No C++ Build Tools)

If you can't install Visual C++ Build Tools, the system will automatically fall back to:
1. **xhtml2pdf** (pure Python, good quality)
2. **pdfkit/wkhtmltopdf** (if installed)
3. **ReportLab** (always works, but may have font issues)

## Verify Installation

After installing Playwright, test it:

```bash
cd backend
python test_pdf_generation.py
```

If Playwright is working, you'll see Tamil text rendered perfectly (no black blocks).

## Troubleshooting

**Error: "greenlet requires Visual C++"**
- Install Visual C++ Build Tools (Option 1 above)

**Error: "chromium not found"**
- Run: `playwright install chromium`

**Still seeing black blocks?**
- Make sure fonts are in `backend/app/fonts/` directory
- Check that Playwright is actually being used (check console output)


