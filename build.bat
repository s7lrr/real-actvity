@echo off
setlocal
cd /d "%~dp0"
echo Building Presence Studio...
py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --onefile --name PresenceStudio main.py
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)
echo.
echo Build complete: dist\PresenceStudio.exe
echo The executable includes its Python dependencies.
pause
