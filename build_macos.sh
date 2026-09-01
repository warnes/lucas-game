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

# The drag-to-install alias.  DO NOT recreate this as a bare `ln -sfn`:
#
#   * `ln -sfn` does NOT refuse when the destination is a real directory -- it
#     exits 0 and nests the link INSIDE it, leaving no alias where one is
#     expected and reporting success.  (Verified 2026-08-31; an earlier comment
#     here claimed the opposite and was wrong.)
#   * A live symlink to /Applications sitting in a build-output directory is a
#     hazard, because `rm -rf dist/*/` -- with a trailing slash, the ordinary
#     way someone clears a build dir -- RESOLVES the symlink and deletes the
#     contents of /Applications itself.  Exit code 0, no output.  Without the
#     trailing slash it merely unlinks.  One character apart.
#
# So: refuse loudly if anything unexpected is there, and verify the result
# rather than trusting ln's exit code.
if [ -e dist/Applications ] && [ ! -L dist/Applications ]; then
    echo "ERROR: dist/Applications exists and is not a symlink." >&2
    echo "       Refusing to touch it -- inspect it by hand." >&2
    exit 1
fi
ln -sfn /Applications dist/Applications
if [ "$(readlink dist/Applications)" != "/Applications" ]; then
    echo "ERROR: dist/Applications is not the expected symlink after ln." >&2
    exit 1
fi

# Build the application
python setup.py py2app

# --------------------------------------------------------------------------
# Post-build verification. py2app exits 0 on both of the failures below, and
# both are invisible until someone launches the bundle from the Dock -- where
# there is no console to print to.  Fail the build instead.
# --------------------------------------------------------------------------
APP="dist/Lucas' Game.app"

# 1. sdl2-compat must NOT be bundled.
#
# `brew install sdl2` now installs sdl2-compat, a SDL2 API shim over SDL3.  Its
# dylib initializer calls -[NSApplication finishLaunching], and when the bundle
# is launched by LaunchServices that runs inside dlopen() while dyld holds the
# loader lock -- AppKit then tries to build the menu bar and deadlocks.  The
# process hangs during `import pygame`, before the window is ever created, so
# the icon bounces forever and nothing appears.  Launching the same binary from
# a terminal does not deadlock, which is what makes this so confusing.
#
# Use pygame's official wheel, which bundles genuine SDL2.
SDL_LIB="$APP/Contents/Frameworks/libSDL2-2.0.0.dylib"
if [ -f "$SDL_LIB" ] && strings "$SDL_LIB" 2>/dev/null | grep -q "sdl2-compat"; then
    echo "" >&2
    echo "ERROR: the bundle contains sdl2-compat, not genuine SDL2." >&2
    echo "       The .app will deadlock on launch from Finder/Dock." >&2
    echo "       Cause: pygame was built from source against Homebrew's sdl2," >&2
    echo "       which is now sdl2-compat (a shim over SDL3)." >&2
    echo "       Fix: build with a Python that has a pygame wheel (3.11-3.13):" >&2
    echo "         pip uninstall -y pygame && pip install pygame" >&2
    exit 1
fi

# 2. _sounddevice_data must be a real directory, not zipped.
# sounddevice finds libportaudio.dylib via _sounddevice_data.__path__, and
# dlopen() cannot read a dylib from inside py2app's zip.  The resulting OSError
# is swallowed by the SOUND_AVAILABLE guard, so the app silently loses audio.
if ! ls "$APP/Contents/Resources/lib/"*"/_sounddevice_data/portaudio-binaries/libportaudio.dylib" >/dev/null 2>&1; then
    echo "" >&2
    echo "ERROR: libportaudio.dylib is not unzipped in the bundle." >&2
    echo "       The .app would run silently with no audio and no error." >&2
    echo "       Fix: keep '_sounddevice_data' and 'cffi' in OPTIONS['packages']." >&2
    exit 1
fi

echo ""
echo "Verified: genuine SDL2 bundled, libportaudio unzipped."
echo ""
echo "Build complete!"
echo "Application created: dist/Lucas' Game.app"
echo ""
echo "To install, drag 'dist/Lucas'\'' Game.app' to your Applications folder"
echo "Or run: open dist/Lucas\\'\\' Game.app"
