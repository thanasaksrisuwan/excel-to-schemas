@echo off
python -m pip install pyinstaller
python -m pyinstaller build.spec
echo Build complete! Check the 'dist' folder for your executable.
pause