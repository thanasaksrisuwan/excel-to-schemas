@echo off
setlocal EnableDelayedExpansion

:: Get current version from package.json if it exists
set CURRENT_VERSION=0.0.0
if exist package.json (
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content package.json | ConvertFrom-Json).version"') do (
        set CURRENT_VERSION=%%a
    )
)

:: Parse current version
for /f "tokens=1,2,3 delims=." %%a in ("%CURRENT_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
    set PATCH=%%c
)

:: Show menu for version increment
echo Current version: %CURRENT_VERSION%
echo Choose version increment:
echo [1] Major (%MAJOR% -^> !MAJOR!+1.0.0)
echo [2] Minor (%MAJOR%.!MINOR! -^> %MAJOR%.!MINOR!+1.0)
echo [3] Patch (%MAJOR%.%MINOR%.!PATCH! -^> %MAJOR%.%MINOR%.!PATCH!+1)
echo [4] Manual input

choice /c 1234 /n /m "Select option (1-4): "

if %ERRORLEVEL%==1 (
    set /a MAJOR+=1
    set MINOR=0
    set PATCH=0
    set VERSION=!MAJOR!.!MINOR!.!PATCH!
) else if %ERRORLEVEL%==2 (
    set /a MINOR+=1
    set PATCH=0
    set VERSION=%MAJOR%.!MINOR!.!PATCH!
) else if %ERRORLEVEL%==3 (
    set /a PATCH+=1
    set VERSION=%MAJOR%.%MINOR%.!PATCH!
) else (
    set /p VERSION="Enter the new version (e.g., 1.0.0): "
)

:: Check if package.json exists and update version
if exist package.json (
    echo Updating package.json version...
    powershell -Command "(Get-Content package.json) -replace '\"version\": \".*\"', '\"version\": \"%VERSION%\"' | Set-Content package.json"
)

:: Git operations
git add .
git commit -m "chore: release version %VERSION%"
git tag v%VERSION%
git push origin main
git push origin v%VERSION%

echo.
echo Release v%VERSION% completed successfully!
echo Don't forget to create a release on GitHub if needed.
pause
