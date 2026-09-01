"""Packaging invariants.

These exist because the two build fixes in fee7c88 had NO automated detection:
a mutation run on 2026-08-31 deleted `distclass=Py2appDistribution` from setup.py
and reverted build_macos.sh to `rm -rf dist`, and the full 74-test suite passed
both times. A fix nothing can detect is one edit from being silently undone.

Copyright (c) 2025 Gregory R. Warnes
License: MIT
"""

import ast
import json
import pathlib
import re

import pytest
import tomllib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _setup_py_options():
    """Read OPTIONS out of setup.py without executing setup()."""
    tree = ast.parse((ROOT / "setup.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", None) == "OPTIONS" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    pytest.fail("OPTIONS not found in setup.py")


def test_py2app_distclass_is_present():
    """py2app aborts with 'install_requires is no longer supported' whenever
    distribution.install_requires is non-empty, and setuptools populates it
    from pyproject.toml's [project].dependencies. Removing the distclass
    breaks build_macos.sh outright, and no other test notices."""
    src = (ROOT / "setup.py").read_text()
    assert "distclass=Py2appDistribution" in src, (
        "setup.py must pass distclass=Py2appDistribution or `python setup.py "
        "py2app` fails: install_requires is no longer supported"
    )
    assert "self.install_requires = []" in src


def test_build_script_does_not_delete_the_dist_directory():
    """`rm -rf dist` destroys the TRACKED dist/Applications symlink that makes
    the drag-to-install work."""
    src = (ROOT / "build_macos.sh").read_text()
    assert not re.search(r"^\s*rm -rf build dist\s*$", src, re.MULTILINE), (
        "build_macos.sh must not `rm -rf dist` -- it deletes the tracked "
        "dist/Applications symlink on every build"
    )
    assert "ln -sfn /Applications dist/Applications" in src


def test_build_script_guards_the_applications_symlink():
    """`ln -sfn` does NOT refuse a real directory -- it exits 0 and nests the
    link inside it. And a live /Applications symlink inside a build directory
    means `rm -rf dist/*/` deletes the contents of /Applications. Both were
    demonstrated on 2026-08-31; the guard is what makes them safe."""
    src = (ROOT / "build_macos.sh").read_text()
    assert "[ ! -L dist/Applications ]" in src, (
        "build_macos.sh must refuse to touch dist/Applications when it is not "
        "a symlink; `ln -sfn` will silently nest inside a real directory"
    )
    assert (
        "readlink dist/Applications" in src
    ), "verify the resulting link rather than trusting ln's exit code"


def test_py2app_packages_cover_every_declared_dependency():
    """The bundle vendors its dependencies; anything declared in pyproject but
    missing from OPTIONS['packages'] is absent from the .app at runtime, and
    py2app exits 0 anyway. That is how the _sounddevice_data silent-audio bug
    shipped."""
    pp = tomllib.loads((ROOT / "pyproject.toml").read_text())
    declared = set(pp["project"]["dependencies"]) | set(
        pp["project"]["optional-dependencies"]["audio"]
    )
    packaged = set(_setup_py_options()["packages"])
    missing = declared - packaged
    assert not missing, f"declared in pyproject but not vendored by py2app: {missing}"


def test_py2app_unzips_sounddevice_data():
    """sounddevice locates libportaudio.dylib via _sounddevice_data.__path__,
    and dlopen() cannot read a dylib from inside py2app's zip."""
    packaged = set(_setup_py_options()["packages"])
    assert "_sounddevice_data" in packaged
    assert "cffi" in packaged


def test_all_five_version_locations_agree():
    """The project rule named four locations; there are five. web/package.json
    had drifted to 1.1.0 while everything else was at 1.1.2."""
    pp = tomllib.loads((ROOT / "pyproject.toml").read_text())
    versions = {"pyproject.toml": pp["project"]["version"]}

    setup_src = (ROOT / "setup.py").read_text()
    versions["setup.py:version="] = re.search(
        r'^\s*version="([^"]+)"', setup_src, re.MULTILINE
    ).group(1)
    for field in ("CFBundleVersion", "CFBundleShortVersionString"):
        versions[f"setup.py:{field}"] = re.search(
            rf'"{field}":\s*"([^"]+)"', setup_src
        ).group(1)

    versions["web/package.json"] = json.loads(
        (ROOT / "web" / "package.json").read_text()
    )["version"]

    assert len(set(versions.values())) == 1, f"version drift: {versions}"


def test_setup_py_does_not_force_py2app_on_every_install():
    """setup_requires=['py2app'] made every `pip install .` -- on Linux, on
    Windows, on the Raspberry Pi kiosk target -- download a macOS-only bundler,
    and fail outright with no network. build_macos.sh installs it explicitly."""
    src = (ROOT / "setup.py").read_text()
    assert "setup_requires" not in src, (
        "setup_requires=['py2app'] penalises every non-macOS install; "
        "build_macos.sh already runs `pip install py2app`"
    )
    assert "pip install py2app" in (ROOT / "build_macos.sh").read_text()


def test_build_script_rejects_sdl2_compat():
    """Regression, reported 2026-09-01: the .app launched from the Dock bounced
    forever and never showed a window, while the same binary run from a terminal
    worked.

    Cause: `brew install sdl2` installs sdl2-compat (a SDL2 shim over SDL3);
    pygame built from source linked against it; py2app bundled it; and its dylib
    initializer calls -[NSApplication finishLaunching], which under
    LaunchServices runs inside dlopen() holding dyld's loader lock and deadlocks
    against AppKit's menu-bar setup -- during `import pygame`, before any window
    exists.

    py2app exits 0 in that state, so only a post-build check can catch it.
    """
    src = (ROOT / "build_macos.sh").read_text()
    assert "sdl2-compat" in src, (
        "build_macos.sh must fail the build when sdl2-compat is bundled; "
        "otherwise the .app deadlocks on Dock launch with no error anywhere"
    )
    assert (
        "strings" in src
    ), "the check must inspect the bundled dylib itself, not merely mention it"
    # Must search the WHOLE bundle. A source build puts SDL2 in
    # Contents/Frameworks/; a wheel build puts it in pygame/.dylibs/. Checking
    # one fixed path passes VACUOUSLY when the library is in the other -- which
    # is exactly how the first version of this guard was wrong.
    assert re.search(
        r'find\s+"\$APP"\s+-name\s+"libSDL2', src
    ), "must find libSDL2 anywhere in the bundle, not at a single fixed path"
    # And it must fail closed: a guard that cannot locate its subject has to
    # refuse, not report success.
    assert re.search(
        r'\[\s+-z\s+"\$SDL_LIBS"\s+\]', src
    ), "must refuse when no libSDL2 is found, rather than passing vacuously"


def test_build_script_verifies_portaudio_is_unzipped():
    """The documented `ls ...portaudio-binaries/` check was never automated, so
    a bundle that had silently lost audio still printed 'Build complete!'."""
    src = (ROOT / "build_macos.sh").read_text()
    assert "portaudio-binaries/libportaudio.dylib" in src
    assert "_sounddevice_data" in src
