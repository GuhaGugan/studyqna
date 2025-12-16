# Windows Installation Fixes

Common issues and solutions when installing on Windows.

## Issue 1: Pillow Installation Error

### Error:
```
ERROR: Failed to build 'Pillow' when getting requirements to build wheel
KeyError: '__version__'
```

### Solution:

**Option 1: Update Pillow Version (Recommended)**

The requirements.txt has been updated to use Pillow 10.1.0 which has pre-built wheels for Windows.

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Option 2: Install Pillow Separately First**

```bash
# Install Pillow with pre-built wheel
pip install Pillow

# Then install other requirements
pip install -r requirements.txt
```

**Option 3: Use Pre-built Binary**

```bash
pip install --only-binary :all: Pillow
pip install -r requirements.txt
```

---

## Issue 2: psycopg2-binary Installation Error

### Error:
```
error: Microsoft Visual C++ 14.0 or greater is required
```

### Solution:

**Option 1: Install Pre-built Binary (Recommended)**

The requirements.txt already uses `psycopg2-binary` which doesn't require compilation.

If you still get errors:
```bash
pip install psycopg2-binary --no-cache-dir
```

**Option 2: Install Visual C++ Build Tools**

1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "C++ build tools" workload
3. Restart terminal and try again

---

## Issue 3: Tesseract OCR Not Found

### Error:
```
TesseractNotFoundError: tesseract is not installed
```

### Solution:

1. **Download Tesseract:**
   - https://github.com/UB-Mannheim/tesseract/wiki
   - Download Windows installer

2. **Install Tesseract:**
   - Default location: `C:\Program Files\Tesseract-OCR`
   - During installation, check "Add to PATH"

3. **Verify Installation:**
   ```bash
   tesseract --version
   ```

4. **If not in PATH, add manually:**
   - Add to System PATH: `C:\Program Files\Tesseract-OCR`
   - Or set in code: `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`

---

## Issue 4: Poppler Not Found

### Error:
```
poppler not found
```

### Solution:

1. **Download Poppler:**
   - https://github.com/oschwartz10612/poppler-windows/releases
   - Download latest release zip

2. **Extract and Add to PATH:**
   - Extract to: `C:\poppler` (or any location)
   - Add `C:\poppler\Library\bin` to System PATH

3. **Verify:**
   ```bash
   pdftoppm -h
   ```

---

## Issue 5: NumPy Installation Error (Python 3.13)

### Error:
```
ERROR: Unknown compiler(s): [['icl'], ['cl'], ['cc'], ['gcc'], ['clang']]
```

### Solution:

**Python 3.13 is very new** - some packages don't have pre-built wheels yet.

**Option 1: Install NumPy separately first (Recommended)**
```bash
# Install NumPy first (will get latest version with wheels)
pip install numpy

# Then install other requirements
pip install -r requirements.txt
```

**Option 2: Use Python 3.11 or 3.12 instead**
- Python 3.11 or 3.12 have better package support
- Most packages have pre-built wheels for these versions

**Option 3: Use the Windows installer script**
```bash
# Run the automated installer
install_windows.bat
```

---

## Issue 6: ultralytics (YOLO) Installation

### Error:
```
Failed to build wheels for ultralytics
```

### Solution:

```bash
# Install with pre-built wheels
pip install ultralytics --no-cache-dir

# Or upgrade pip first
python -m pip install --upgrade pip
pip install ultralytics
```

---

## Issue 6: General Build Errors

### Solution: Install Build Tools

```bash
# Install wheel and setuptools
pip install --upgrade pip wheel setuptools

# Then install requirements
pip install -r requirements.txt
```

---

## Complete Windows Installation Steps

### Step 1: Install System Dependencies

1. **Tesseract OCR:**
   - Download: https://github.com/UB-Mannheim/tesseract/wiki
   - Install and add to PATH

2. **Poppler:**
   - Download: https://github.com/oschwartz10612/poppler-windows/releases
   - Extract and add `Library\bin` to PATH

### Step 2: Python Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip wheel setuptools

# Install requirements
pip install -r requirements.txt
```

### Step 3: If Pillow Fails

```bash
# Install Pillow separately first
pip install Pillow

# Then continue with other packages
pip install -r requirements.txt --no-deps
pip install -r requirements.txt
```

---

## Alternative: Use Pre-built Wheels Only

If you continue having build issues:

```bash
# Install only packages with pre-built wheels
pip install --only-binary :all: -r requirements.txt
```

Note: This may skip some packages. Install them individually if needed.

---

## Quick Fix Script

Create a file `install_windows.bat`:

```batch
@echo off
echo Installing StudyQnA Backend on Windows...

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip
python -m pip install --upgrade pip wheel setuptools

REM Install Pillow first (common issue)
pip install Pillow

REM Install other requirements
pip install -r requirements.txt

echo Installation complete!
pause
```

Run: `install_windows.bat`

---

## Still Having Issues?

1. **Check Python version:**
   ```bash
   python --version
   # Should be 3.9 or higher
   ```

2. **Use 64-bit Python:**
   - Ensure you're using 64-bit Python (not 32-bit)

3. **Try installing packages individually:**
   ```bash
   pip install fastapi
   pip install uvicorn[standard]
   pip install sqlalchemy
   # etc.
   ```

4. **Check for conflicting packages:**
   ```bash
   pip list
   pip uninstall <conflicting-package>
   ```

5. **Use Docker instead:**
   - Docker handles all dependencies automatically
   - See DOCKER_SETUP.md

---

## Recommended: Use Docker on Windows

Docker Desktop for Windows handles all these issues automatically:

```bash
# Install Docker Desktop
# Then use Docker setup
docker-compose up -d postgres
```

See DOCKER_SETUP.md for complete Docker instructions.

