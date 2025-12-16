@echo off
echo Installing StudyQnA Backend Requirements on Windows...
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip wheel setuptools
echo.

REM Install Pillow first (common Windows issue)
echo Installing Pillow...
pip install Pillow
echo.

REM Install other requirements (skip Pillow if already installed)
echo Installing other requirements...
pip install -r requirements.txt
echo.

echo.
echo Installation complete!
echo.
pause


