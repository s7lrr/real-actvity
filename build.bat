@echo off
setlocal
cd /d "%~dp0"
echo Installing build requirements...
py -m pip install --upgrade pip
if errorlevel 1 goto error
py -m pip install -r requirements.txt
if errorlevel 1 goto error
echo Building Presence Studio...
py -m PyInstaller --noconfirm --clean --windowed --onefile --name PresenceStudio --collect-all pypresence main.py
if errorlevel 1 goto error
echo.
echo Build complete: dist\PresenceStudio.exe
pause
exit /b 0
:error
echo.
echo Build failed. Check the error messages above.
pause
exit /b 1
