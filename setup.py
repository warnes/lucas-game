"""
Setup script for Lucas' Game
Copyright (c) 2025 Gregory R. Warnes
"""

from setuptools import setup

APP = ["lucas_game.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "icon.icns",
    "plist": {
        "CFBundleName": "Lucas' Game",
        "CFBundleDisplayName": "Lucas' Game",
        "CFBundleIdentifier": "com.gregorywarnes.lucasgame",
        "CFBundleVersion": "1.1.0",
        "CFBundleShortVersionString": "1.1.0",
        "NSHumanReadableCopyright": "© 2025 Gregory R. Warnes",
        "NSHighResolutionCapable": True,
    },
    "packages": ["pygame", "numpy", "sounddevice", "platformdirs"],
}

setup(
    name="Lucas' Game",
    version="1.1.0",
    author="Gregory R. Warnes",
    description="Fullscreen keyboard game with configurable exit shortcut and optional audio",
    license="MIT",
    app=APP,
    py_modules=["lucas_game"],
    data_files=DATA_FILES,
    install_requires=["pygame", "platformdirs"],
    extras_require={"audio": ["numpy", "sounddevice"]},
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
