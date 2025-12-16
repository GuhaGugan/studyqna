@echo off
REM Migration script to add subject column to uploads table
REM This script activates the virtual environment and runs the migration

echo 🔄 Starting subject column migration...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please create a virtual environment first:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run migration
echo Running migration...
python migrations/add_subject_column.py

REM Check exit code
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Migration failed!
    pause
    exit /b 1
)

echo.
echo ✅ Migration completed!
pause


