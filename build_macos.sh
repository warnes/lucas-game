#!/bin/bash
# Build script for Lucas' Game macOS application
# Copyright (c) 2025 Gregory R. Warnes

set -e

echo "Building Lucas' Game for macOS..."

# Activate virtual environment
source venv/bin/activate

# Install py2app if not already installed
pip install py2app

# Generate icon if it doesn't exist
if [ ! -f icon.icns ]; then
    echo "Generating icon..."
    python create_icon.py
    
    # Create iconset
    mkdir -p icon.iconset
    sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
    sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
    sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
    sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
    sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
    sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
    sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
    sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
    sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
    sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png
    
    # Convert to .icns
    iconutil -c icns icon.iconset
    rm -rf icon.iconset
    echo "Icon created: icon.icns"
fi

# Clean previous builds.  Remove the bundle rather than the whole dist/
# directory: dist/Applications is a tracked symlink to /Applications (it makes
# the drag-and-drop install work), and "rm -rf dist" deletes it every build.
rm -rf build
rm -rf "dist/Lucas' Game.app"
mkdir -p dist
# -f -n so this is idempotent and also repairs a broken/stale link.  It will
# fail rather than clobber if dist/Applications is somehow a real directory.
ln -sfn /Applications dist/Applications

# Build the application
python setup.py py2app

echo ""
echo "Build complete!"
echo "Application created: dist/Lucas' Game.app"
echo ""
echo "To install, drag 'dist/Lucas'\'' Game.app' to your Applications folder"
echo "Or run: open dist/Lucas\\'\\' Game.app"
