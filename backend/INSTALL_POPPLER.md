# Installing Poppler Utilities for Image-Based PDF OCR

## Why Poppler is Required

Poppler utilities are required for converting PDF pages to images, which is necessary for OCR processing of image-based/scanned PDFs.

## Installation Instructions

### Ubuntu/Debian (Lightsail/EC2)
```bash
sudo apt-get update
sudo apt-get install -y poppler-utils
```

### Verify Installation
```bash
pdftoppm -v
# Should output version information
```

### CentOS/RHEL
```bash
sudo yum install poppler-utils
# or for newer versions:
sudo dnf install poppler-utils
```

### Windows Server
1. Download Poppler for Windows from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to a folder (e.g., `C:\poppler`)
3. Add to PATH or set environment variable:
   ```powershell
   $env:PATH += ";C:\poppler\Library\bin"
   ```

### macOS
```bash
brew install poppler
```

## Testing OCR Functionality

After installation, test with:
```bash
python -c "from pdf2image import convert_from_bytes; print('Poppler is working!')"
```

## Troubleshooting

If you still get errors after installing poppler:

1. **Check if poppler is in PATH:**
   ```bash
   which pdftoppm  # Linux/Mac
   where pdftoppm  # Windows
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

# Install poppler
sudo apt-get install -y poppler-utils

# Verify installation
pdftoppm -v

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
RUN apt-get update && apt-get install -y poppler-utils && rm -rf /var/lib/apt/lists/*

# For Alpine-based image
RUN apk add --no-cache poppler-utils
```

