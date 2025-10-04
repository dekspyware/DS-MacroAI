@echo off
REM Build Python Macro to EXE

set SCRIPT_NAME=macro-gui.py

REM Remove previous builds
if exist build rmdir /s /q build
if exist %SCRIPT_NAME:.py=.exe% del %SCRIPT_NAME:.py=.exe%

REM Build EXE WITHOUT --noconsole
pyinstaller --onefile %SCRIPT_NAME%

echo.
echo Build complete! Check the 'dist' folder.
pause
