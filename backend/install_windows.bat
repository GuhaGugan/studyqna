@echo off
echo ========================================
echo StudyQnA Backend - Windows Installation
echo ========================================
echo.

REM Activate virtual environment
if not exist venv\Scripts\activate.bat (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv venv
    pause
    exit /b 1
)

call venv\Scripts\activate

REM Upgrade pip and build tools
echo [1/5] Upgrading pip and build tools...
python -m pip install --upgrade pip wheel setuptools
echo.

REM Install NumPy first (has pre-built wheels)
echo [2/5] Installing NumPy (pre-built wheel)...
pip install numpy
echo.

REM Install Pillow (has pre-built wheels)
echo [3/5] Installing Pillow (pre-built wheel)...
pip install Pillow
echo.

REM Install other packages that need compilation separately
echo [4/5] Installing packages with pre-built wheels...
pip install opencv-python
echo.

REM Install pydantic separately (needs newer version for Python 3.13)
echo Installing pydantic (latest version for Python 3.13)...
pip install "pydantic>=2.9.0" "pydantic-settings>=2.5.0"
echo.

REM Install remaining requirements
echo [5/5] Installing remaining requirements...
pip install -r requirements.txt
echo.

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create .env file: copy ENV_TEMPLATE.txt .env
echo 2. Edit .env with your settings
echo 3. Initialize database: python init_db.py
echo 4. Start server: python run.py
echo.
pause

