@echo off
echo 🚀 Building secure executable (no source code exposed)...

:: App settings
set APP_NAME=screenshot
set MAIN_FILE=screenshot.py
set DIST_DIR=secure_dist
set BUILD_DIR=build_temp
set SPEC_DIR=build_temp

:: Common build options
::Không bật terminal khi run file.exe
::set BUILD_OPTIONS=--onefile --windowed --distpath=%DIST_DIR% --workpath=%BUILD_DIR% --specpath=%SPEC_DIR% --hidden-import=browser_path --hidden-import=utils_scroll

::Bật terminal khi run file.exe
set BUILD_OPTIONS=--onefile --distpath=%DIST_DIR% --workpath=%BUILD_DIR% --specpath=%SPEC_DIR% --hidden-import=browser_path --hidden-import=utils_scroll


:: Ensure pyinstaller is installed
python -m pip install --user pyinstaller

:: Build executable
python -m PyInstaller %BUILD_OPTIONS% --name=%APP_NAME% %MAIN_FILE%

:: Clean up build folder
rmdir /s /q %BUILD_DIR%

:: Check result
if exist %DIST_DIR%\%APP_NAME%.exe (
    echo ✅ Secure executable created: %DIST_DIR%\%APP_NAME%.exe
) else (
    echo ❌ Build failed. Check error messages above.
)
pause