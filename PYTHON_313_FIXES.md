# Python 3.13 Compatibility Fixes

Python 3.13 is very new, and some packages don't have pre-built wheels yet. Here are fixes for common issues.

## Issue: pydantic-core Building from Source

### Error:
```
pydantic-core==2.14.1 requires Rust to compile
Cargo, the Rust package manager, is not installed or is not on PATH
```

### Solution 1: Update pydantic (Recommended)

Install a newer version of pydantic that has pre-built wheels for Python 3.13:

```bash
# Install newer pydantic version
pip install "pydantic>=2.9.0" "pydantic-settings>=2.5.0"

# Then install other requirements
pip install -r requirements.txt
```

### Solution 2: Install Rust (If you need to build from source)

1. **Download Rust:**
   - Visit: https://rustup.rs/
   - Download and run `rustup-init.exe`

2. **Install Rust:**
   - Follow the installer prompts
   - Restart your terminal after installation

3. **Verify:**
   ```bash
   cargo --version
   rustc --version
   ```

4. **Then install:**
   ```bash
   pip install -r requirements.txt
   ```

### Solution 3: Use Python 3.11 or 3.12 (Easiest)

Python 3.11 and 3.12 have better package support:

```bash
# Create new virtual environment with Python 3.11 or 3.12
python3.11 -m venv venv
# or
python3.12 -m venv venv

# Activate and install
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Quick Fix Commands

### For Python 3.13:

```bash
# 1. Install newer pydantic first
pip install "pydantic>=2.9.0" "pydantic-settings>=2.5.0"

# 2. Install other packages
pip install -r requirements.txt
```

### Or use updated requirements:

I've updated `requirements.txt` to use `pydantic>=2.5.0` which will get a newer version with wheels.

---

## Recommended: Use Python 3.12

For best compatibility, use Python 3.12:

1. **Download Python 3.12:**
   - https://www.python.org/downloads/
   - Choose Python 3.12.x

2. **Create new venv:**
   ```bash
   py -3.12 -m venv venv
   venv\Scripts\activate
   ```

3. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

This will work without any issues!

---

## Check Python Version

```bash
python --version
```

If it shows Python 3.13, consider using 3.11 or 3.12 for better package support.

---

## Summary

**Best Solution:** Use Python 3.11 or 3.12 instead of 3.13

**Quick Fix for 3.13:** Install newer pydantic version first:
```bash
pip install "pydantic>=2.9.0"
pip install -r requirements.txt
```


