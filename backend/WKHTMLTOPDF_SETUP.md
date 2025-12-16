# wkhtmltopdf Installation Guide

`pdfkit` requires `wkhtmltopdf` binary to be installed on your system.

## Windows Installation

1. **Download wkhtmltopdf:**
   - Visit: https://wkhtmltopdf.org/downloads.html
   - Download the Windows installer (64-bit recommended)
   - Example: `wkhtmltopdf-0.12.6-1.msvc2015-win64.exe`

2. **Install:**
   - Run the installer
   - Default installation path: `C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe`
   - Make sure to check "Add to PATH" during installation (or add manually)

3. **Verify Installation:**
   ```bash
   wkhtmltopdf --version
   ```

4. **If not in PATH:**
   - The code will automatically try common installation paths
   - Or set environment variable: `WKHTMLTOPDF_BINARY` pointing to the exe

## Linux Installation

```bash
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf

# CentOS/RHEL
sudo yum install wkhtmltopdf
```

## macOS Installation

```bash
brew install wkhtmltopdf
```

## Alternative: Use Playwright (No Binary Required)

If you prefer not to install wkhtmltopdf, we can switch to Playwright which doesn't require external binaries.

## Testing

After installation, test the PDF generation:

```bash
cd backend
python test_pdf_generation.py
```


