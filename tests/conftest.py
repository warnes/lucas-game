"""Pytest configuration for Lucas' Game.

Copyright (c) 2025 Gregory R. Warnes
License: MIT
"""

import os

# lucas_game opens a fullscreen display at import time, so the dummy SDL video
# driver must be selected before the module is imported anywhere.  Setting it
# here (conftest is imported before test modules) keeps the suite headless and
# stops it from taking over the developer's screen.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest  # noqa: E402

import lucas_game  # noqa: E402


@pytest.fixture(autouse=True)
def pygame_ready():
    """Guarantee a live pygame display for every test.

    ``lucas_game.main()`` ends with ``pygame.quit()``, which tears down the
    video subsystem process-wide.  Without this, every test ordered after the
    end-to-end one fails with "video system not initialized".  Re-binding
    ``lucas_game.screen`` matters too: the surface created before ``quit()``
    is dead, and the draw helpers and ``main()`` both use that global.
    """
    import pygame

    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    if not pygame.font.get_init():
        pygame.font.init()
    if pygame.display.get_surface() is None:
        lucas_game.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.event.clear()
    pygame.key.set_mods(0)
    yield


@pytest.fixture
def default_config():
    """A fresh copy of the shipped default configuration."""
    import copy

    return copy.deepcopy(lucas_game.DEFAULT_CONFIG)


@pytest.fixture
def shortcut():
    """Build an exit_shortcut config dict."""

    def _make(key, ctrl=False, shift=False, alt=False):
        return {"exit_shortcut": {"key": key, "ctrl": ctrl, "shift": shift, "alt": alt}}

    return _make


@pytest.fixture
def mods():
    """Set live pygame modifier state for the duration of a test.

    ``check_exit_shortcut`` reads ``pygame.key.get_mods()`` rather than
    ``event.mod``, so tests must set the real modifier state.
    """
    import pygame

    def _set(value):
        pygame.key.set_mods(value)

    yield _set
    if pygame.display.get_init():
        pygame.key.set_mods(0)
