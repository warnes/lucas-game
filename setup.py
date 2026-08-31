"""
Setup script for Lucas' Game
Copyright (c) 2025 Gregory R. Warnes
"""

from setuptools import setup
from setuptools.dist import Distribution


class Py2appDistribution(Distribution):
    """Distribution that hides ``install_requires`` from py2app.

    py2app aborts with "error: install_requires is no longer supported"
    whenever ``distribution.install_requires`` is non-empty
    (``py2app/build_app.py``).  Modern setuptools populates that attribute
    automatically from ``pyproject.toml``'s ``[project].dependencies``, so
    simply keeping ``install_requires`` out of ``setup()`` is not enough --
    the value arrives from the TOML file regardless.

    Runtime dependencies are declared once, in ``pyproject.toml``, where pip
    needs them.  The ``.app`` bundle vendors those packages outright (see
    ``OPTIONS["packages"]``), so the bundle build has no use for the list.
    Clearing it here therefore affects only ``python setup.py py2app``.
    """

    def parse_config_files(self, *args, **kwargs):
        super().parse_config_files(*args, **kwargs)
        self.install_requires = []


APP = ["lucas_game.py"]
DATA_FILES = []
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "icon.icns",
    "plist": {
        "CFBundleName": "Lucas' Game",
        "CFBundleDisplayName": "Lucas' Game",
        "CFBundleIdentifier": "com.gregorywarnes.lucasgame",
        "CFBundleVersion": "1.1.3",
        "CFBundleShortVersionString": "1.1.3",
        "NSHumanReadableCopyright": "© 2025 Gregory R. Warnes",
        "NSHighResolutionCapable": True,
    },
    # Listing a package here makes py2app copy it as a real directory tree
    # instead of zipping it into python39.zip.  _sounddevice_data must be
    # unzipped: sounddevice locates libportaudio.dylib via its __path__ and
    # dlopen() cannot load a dylib from inside a zip archive.
    "packages": [
        "pygame",
        "numpy",
        "sounddevice",
        "platformdirs",
        "cffi",
        "_sounddevice_data",
    ],
    "includes": ["_sounddevice", "_cffi_backend"],
}

setup(
    name="Lucas' Game",
    version="1.1.3",
    author="Gregory R. Warnes",
    description="Fullscreen keyboard game with configurable exit shortcut and optional audio",
    license="MIT",
    app=APP,
    py_modules=["lucas_game"],
    data_files=DATA_FILES,
    # Runtime dependencies live in pyproject.toml ([project].dependencies and
    # [project.optional-dependencies].audio).  Do not repeat them here -- and
    # note that omitting them is not sufficient on its own, because setuptools
    # copies them out of pyproject.toml into install_requires, which py2app
    # rejects.  Py2appDistribution above is what actually clears them.
    options={"py2app": OPTIONS},
    distclass=Py2appDistribution,
)
