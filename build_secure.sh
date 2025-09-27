#!/bin/bash
echo "🚀 Building secure executable (no source code exposed)..."

# Detect OS
OS=$(uname -s)

# Install PyInstaller if not available
python3 -m pip install --user pyinstaller

# Add pip install path to PATH
export PATH="$HOME/.local/bin:$PATH"

# Default values
APP_NAME="screenshot"
MAIN_FILE="screenshot.py"

# Common build options
BUILD_OPTIONS="--onefile --windowed --distpath=./secure_dist --workpath=./build_temp --specpath=./build_temp --hidden-import=browser_path --hidden-import=utils_scroll"

# Detect OS type
case "$OS" in
    Linux*)
        echo "🟢 Detected Linux"
        python3 -m PyInstaller $BUILD_OPTIONS --name=$APP_NAME $MAIN_FILE
        TARGET_FILE="secure_dist/$APP_NAME"
        ;;
    Darwin*)
        echo "🍎 Detected macOS"
        python3 -m PyInstaller $BUILD_OPTIONS --name=$APP_NAME $MAIN_FILE
        TARGET_FILE="secure_dist/$APP_NAME"
        ;;
    MINGW*|MSYS*|CYGWIN*|Windows*)
        echo "🟦 Detected Windows"
        pyinstaller $BUILD_OPTIONS --name=$APP_NAME $MAIN_FILE
        TARGET_FILE="secure_dist/$APP_NAME.exe"
        ;;
    *)
        echo "❌ Unsupported OS: $OS"
        exit 1
        ;;
esac

# Clean up build files
rm -rf build_temp

# Check result
if [ -f "$TARGET_FILE" ]; then
    echo "✅ Secure executable created: $TARGET_FILE"
    echo "📁 File size: $(du -h "$TARGET_FILE" | cut -f1)"
else
    echo "❌ Build failed. Check error messages above."
    echo "👉 Try: python3 -m pip install --user pyinstaller"
fi