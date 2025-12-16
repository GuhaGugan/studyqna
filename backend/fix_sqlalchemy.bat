@echo off
echo Fixing SQLAlchemy for Python 3.13...
echo.

call venv\Scripts\activate

echo Upgrading SQLAlchemy to version compatible with Python 3.13...
pip install --upgrade "sqlalchemy>=2.0.36"

echo.
echo SQLAlchemy upgraded! Now try: python init_db.py
echo.
pause


