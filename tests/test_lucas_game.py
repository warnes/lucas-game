"""Tests for Lucas' Game.

Runs headlessly via SDL's dummy video driver (see conftest.py).

Copyright (c) 2025 Gregory R. Warnes
License: MIT
"""

import copy
import json
import threading
import time

import pygame
import pytest

import lucas_game as lg

# ---------------------------------------------------------------------------
# Key-name resolution
# ---------------------------------------------------------------------------


class TestResolveKeyName:
    """pygame cases its key constants inconsistently: letters are lowercase
    (K_q) while everything else is uppercase (K_ESCAPE, K_F10)."""

    @pytest.mark.parametrize(
        "name,expected",
        [
            ("ESCAPE", pygame.K_ESCAPE),
            ("RETURN", pygame.K_RETURN),
            ("F10", pygame.K_F10),
            ("SPACE", pygame.K_SPACE),
            ("TAB", pygame.K_TAB),
            ("1", pygame.K_1),
            ("q", pygame.K_q),
            ("a", pygame.K_a),
        ],
    )
    def test_documented_spellings_resolve(self, name, expected):
        key, resolved = lg.resolve_key_name(name)
        assert key == expected
        assert resolved is not None

    @pytest.mark.parametrize("name", ["Q", "A", "Z"])
    def test_uppercase_letters_resolve(self, name):
        """Regression: the README advertises "Q"; pygame only exports K_q.

        This used to fall through to ESCAPE silently, so the on-screen hint
        said "Ctrl+Q" while the key that actually exited was Escape.
        """
        assert not hasattr(pygame, f"K_{name}"), "premise: pygame has no K_Q"
        key, resolved = lg.resolve_key_name(name)
        assert key == getattr(pygame, f"K_{name.lower()}")
        assert resolved == name.lower()

    @pytest.mark.parametrize("name", ["escape", "return", "f10", "space"])
    def test_lowercase_non_letter_names_resolve(self, name):
        key, resolved = lg.resolve_key_name(name)
        assert key == getattr(pygame, f"K_{name.upper()}")
        assert resolved == name.upper()

    @pytest.mark.parametrize("name", ["K_ESCAPE", "K_Q", "BOGUS", "", None, 42])
    def test_unresolvable_names_fall_back_to_escape(self, name):
        key, resolved = lg.resolve_key_name(name)
        assert key == pygame.K_ESCAPE
        assert resolved is None, "an unresolvable name must not claim success"

    def test_unresolvable_name_warns_once(self, capsys):
        lg._KEY_RESOLUTION_WARNED.discard("TOTALLY_BOGUS")
        lg.resolve_key_name("TOTALLY_BOGUS")
        first = capsys.readouterr().out
        lg.resolve_key_name("TOTALLY_BOGUS")
        second = capsys.readouterr().out
        assert "TOTALLY_BOGUS" in first, "first bad lookup must warn"
        assert second == "", "repeat lookups must not spam the console"


# ---------------------------------------------------------------------------
# Exit shortcut matching
# ---------------------------------------------------------------------------


def keydown(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


CTRL_SHIFT = pygame.KMOD_LCTRL | pygame.KMOD_LSHIFT


class TestCheckExitShortcut:
    def test_default_combo_exits(self, default_config, mods):
        mods(CTRL_SHIFT)
        assert lg.check_exit_shortcut(keydown(pygame.K_ESCAPE), default_config)

    def test_bare_escape_does_not_exit(self, default_config, mods):
        """Kiosk safety: a child pressing Escape must not end the game."""
        mods(0)
        assert not lg.check_exit_shortcut(keydown(pygame.K_ESCAPE), default_config)

    @pytest.mark.parametrize(
        "mod_state", [0, pygame.KMOD_LCTRL, pygame.KMOD_LSHIFT, pygame.KMOD_LALT]
    )
    def test_partial_modifiers_do_not_exit(self, default_config, mods, mod_state):
        mods(mod_state)
        assert not lg.check_exit_shortcut(keydown(pygame.K_ESCAPE), default_config)

    def test_extra_modifier_does_not_exit(self, default_config, mods):
        """alt:false means Alt must be absent, not merely unchecked."""
        mods(CTRL_SHIFT | pygame.KMOD_LALT)
        assert not lg.check_exit_shortcut(keydown(pygame.K_ESCAPE), default_config)

    def test_other_key_with_right_modifiers_does_not_exit(self, default_config, mods):
        mods(CTRL_SHIFT)
        assert not lg.check_exit_shortcut(keydown(pygame.K_a), default_config)

    def test_custom_uppercase_letter_shortcut(self, shortcut, mods):
        """Regression for the README's "Q" example."""
        cfg = shortcut("Q", ctrl=True)
        mods(pygame.KMOD_LCTRL)
        assert lg.check_exit_shortcut(keydown(pygame.K_q), cfg)
        assert not lg.check_exit_shortcut(
            keydown(pygame.K_ESCAPE), cfg
        ), "Escape must not exit a Ctrl+Q shortcut"

    def test_k_prefix_is_rejected(self, shortcut, mods):
        """The README documents the K_ prefix as incorrect."""
        cfg = shortcut("K_Q", ctrl=True)
        mods(pygame.KMOD_LCTRL)
        assert not lg.check_exit_shortcut(keydown(pygame.K_q), cfg)

    @pytest.mark.parametrize(
        "cfg",
        [
            {},
            {"exit_shortcut": {}},
            {"exit_shortcut": "not-a-dict"},
            {"exit_shortcut": {"key": None}},
            None,
        ],
    )
    def test_malformed_config_does_not_raise(self, cfg, mods):
        """Regression: an unbound `shortcut` used to raise NameError here,
        which the modifier-check except clause did not catch."""
        mods(CTRL_SHIFT)
        result = lg.check_exit_shortcut(keydown(pygame.K_ESCAPE), cfg)
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Exit-hint display
# ---------------------------------------------------------------------------


class TestExitShortcutDisplay:
    def test_default_display(self, default_config):
        assert lg.get_exit_shortcut_display(default_config) == "Ctrl+Shift+Esc"

    def test_custom_display(self, shortcut):
        assert lg.get_exit_shortcut_display(shortcut("Q", ctrl=True)) == "Ctrl+Q"
        assert lg.get_exit_shortcut_display(shortcut("F10", alt=True)) == "Alt+F10"

    def test_hint_reports_the_key_that_actually_exits(self, shortcut, mods):
        """An unresolvable key falls back to Escape; the hint must say so
        rather than advertising a shortcut that does nothing."""
        cfg = shortcut("BOGUS", ctrl=True, shift=True)
        assert lg.get_exit_shortcut_display(cfg) == "Ctrl+Shift+Esc"
        mods(CTRL_SHIFT)
        assert lg.check_exit_shortcut(keydown(pygame.K_ESCAPE), cfg)

    def test_malformed_config_falls_back(self):
        assert lg.get_exit_shortcut_display({}) == "Ctrl+Shift+Esc"
        assert lg.get_exit_shortcut_display(None) == "Ctrl+Shift+Esc"


# ---------------------------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------------------------


class TestLoadConfig:
    @pytest.fixture(autouse=True)
    def _isolate_config(self, tmp_path, monkeypatch):
        """Never touch the developer's real config file."""
        cfg = tmp_path / "config.json"
        monkeypatch.setattr(lg, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(lg, "CONFIG_FILE", cfg)
        self.cfg = cfg

    def test_creates_default_when_missing(self):
        assert not self.cfg.exists()
        loaded = lg.load_config()
        assert loaded == lg.DEFAULT_CONFIG
        assert self.cfg.exists(), "a missing config must be written out"

    def test_reads_back_valid_config(self):
        self.cfg.write_text(
            json.dumps(
                {
                    "exit_shortcut": {
                        "key": "F10",
                        "ctrl": False,
                        "shift": False,
                        "alt": True,
                    }
                }
            )
        )
        loaded = lg.load_config()
        assert loaded["exit_shortcut"]["key"] == "F10"
        assert loaded["exit_shortcut"]["alt"] is True

    @pytest.mark.parametrize(
        "content",
        [
            "{ not json at all",
            "[]",
            '{"exit_shortcut": {"key": 42, "ctrl": "yes"}}',
            '{"wrong_section": {}}',
        ],
    )
    def test_malformed_config_falls_back_to_defaults(self, content):
        self.cfg.write_text(content)
        assert lg.load_config() == lg.DEFAULT_CONFIG

    @pytest.mark.parametrize(
        "content",
        [
            # exit_shortcut present but not a dict -> .get() on a non-dict
            '{"exit_shortcut": "hello"}',
            '{"exit_shortcut": [1, 2, 3]}',
            '{"exit_shortcut": 5}',
            '{"exit_shortcut": null}',
            # JSON root is not a container -> `in` raises TypeError
            "5",
            "null",
            "true",
            '"hello"',
        ],
    )
    def test_wrongly_typed_config_does_not_crash(self, content):
        """Regression: these raised AttributeError/TypeError out of
        load_config(), which runs at MODULE SCOPE -- so a malformed config
        file crashed the game on startup, before the title screen.

        The README promises the game falls back to defaults and rewrites the
        file when the config is malformed or wrongly typed. It must.
        """
        self.cfg.write_text(content)
        assert lg.load_config() == lg.DEFAULT_CONFIG
        assert json.loads(self.cfg.read_text()) == lg.DEFAULT_CONFIG

    def test_malformed_config_is_rewritten(self):
        self.cfg.write_text("{ broken")
        lg.load_config()
        assert json.loads(self.cfg.read_text()) == lg.DEFAULT_CONFIG


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


class TestRendering:
    def test_generate_random_color_in_range(self):
        for _ in range(500):
            color = lg.generate_random_color()
            assert len(color) == 3
            assert all(isinstance(c, int) and 0 <= c <= 255 for c in color)

    @pytest.mark.parametrize(
        "key",
        [
            pygame.K_a,
            pygame.K_z,
            pygame.K_SPACE,
            pygame.K_RETURN,
            pygame.K_F1,
            pygame.K_1,
            pygame.K_UP,
            pygame.K_LSHIFT,
        ],
    )
    def test_get_key_name_returns_label(self, key):
        name = lg.get_key_name(key)
        assert isinstance(name, str) and name

    def test_draw_helpers_do_not_raise(self, default_config):
        lg.screen.fill((0, 0, 0))
        lg.draw_key(lg.screen, "A", (10, 20, 30))
        lg.draw_exit_hint(lg.screen, default_config)

    def test_draw_exit_hint_paints_bottom_right(self, default_config):
        """The hint is the parents' way out; it must actually be drawn."""
        lg.screen.fill((0, 0, 0))
        before = lg.screen.get_at(
            (lg.screen.get_width() - 20, lg.screen.get_height() - 20)
        )
        lg.draw_exit_hint(lg.screen, default_config)
        after = lg.screen.get_at(
            (lg.screen.get_width() - 20, lg.screen.get_height() - 20)
        )
        assert before != after, "nothing was painted in the bottom-right corner"


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not lg.SOUND_AVAILABLE, reason="audio stack unavailable")
class TestAudio:
    def test_tone_length_and_dtype(self):
        tone = lg.generate_tone(440.0, duration=0.5, sample_rate=22050)
        assert tone is not None
        assert len(tone) == int(0.5 * 22050)
        assert str(tone.dtype) == "int16"

    def test_tone_is_faded(self):
        """Fade in/out exists to avoid clicks."""
        tone = lg.generate_tone(440.0, duration=0.5, sample_rate=22050)
        assert tone is not None
        assert abs(int(tone[0])) < 100
        assert abs(int(tone[-1])) < 100
        assert abs(int(tone[len(tone) // 4])) > 1000, "middle should be loud"


def test_generate_tone_returns_none_without_sound(monkeypatch):
    monkeypatch.setattr(lg, "SOUND_AVAILABLE", False)
    assert lg.generate_tone(440.0) is None


def test_play_random_tone_is_silent_fallback(monkeypatch, capsys):
    """Visual-only mode prints a note glyph instead of playing."""
    monkeypatch.setattr(lg, "SOUND_AVAILABLE", False)
    lg.play_random_tone()
    assert "♪" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# End-to-end event loop
# ---------------------------------------------------------------------------


def test_main_runs_title_then_keypress_then_exit(monkeypatch):
    """Drive main() through its whole lifecycle without a real display."""
    calls = []
    monkeypatch.setattr(lg, "_suppress_media_keys", lambda: calls.append("suppress"))
    monkeypatch.setattr(lg, "play_random_tone", lambda: calls.append("tone"))
    # main() reads the MODULE-LEVEL `config`, which is loaded at import time
    # from the developer's real config file. Without pinning it, this test
    # asserts a property of whoever's machine it runs on: a developer whose
    # config sets a different shortcut gets a red suite on unmodified code.
    monkeypatch.setattr(lg, "config", copy.deepcopy(lg.DEFAULT_CONFIG))

    def feeder():
        # show_title_screen consumes a whole event.get() batch and keeps only
        # the first KEYDOWN, so events must be delivered one at a time.
        time.sleep(0.2)
        pygame.event.post(keydown(pygame.K_b))
        time.sleep(0.4)
        pygame.event.post(keydown(pygame.K_c))
        time.sleep(0.4)
        pygame.key.set_mods(CTRL_SHIFT)
        pygame.event.post(keydown(pygame.K_ESCAPE))

    pygame.event.clear()
    done = []
    threading.Thread(target=feeder, daemon=True).start()
    runner = threading.Thread(
        target=lambda: (lg.main(), done.append(True)), daemon=True
    )
    runner.start()
    runner.join(timeout=15)
    # NB: main() has now called pygame.quit(); the autouse pygame_ready
    # fixture restores the display for subsequent tests.

    # A timed-out main() thread keeps spinning on the SHARED pygame event queue
    # for the rest of the session, stealing events posted by later tests and
    # turning this test's failure into someone else's 133-second hang. Assert it
    # is dead before going any further.
    assert not runner.is_alive(), (
        "main() thread is still running and will corrupt every later test that "
        "uses the pygame event queue"
    )
    assert done, "main() did not return; the exit shortcut was not honored"
    assert calls[0] == "suppress", "media keys must be suppressed on start"
    assert (
        calls.count("tone") == 2
    ), f"expected a tone for the title key and the gameplay key, got {calls}"


def test_title_screen_exit_shortcut_returns_none():
    """The exit shortcut must work on the title screen too."""
    pygame.event.clear()
    pygame.key.set_mods(CTRL_SHIFT)
    pygame.event.post(keydown(pygame.K_ESCAPE))
    try:
        result = lg.show_title_screen(lg.screen, lg.DEFAULT_CONFIG)
    finally:
        pygame.key.set_mods(0)
    assert result is None


def test_ignored_keys_are_skipped_on_title_screen():
    """F13 is where macOS media keys get remapped; it must not start the game."""
    pygame.event.clear()
    pygame.key.set_mods(0)
    pygame.event.post(keydown(pygame.K_F13))
    pygame.event.post(keydown(pygame.K_g))
    event = lg.show_title_screen(lg.screen, lg.DEFAULT_CONFIG)
    assert event is not None
    assert event.key == pygame.K_g, "F13 should have been ignored, not consumed"


# ---------------------------------------------------------------------------
# Regressions from the 2026-08-31 committee review.
# Each of these was demonstrated to FAIL against the code before its fix.
# ---------------------------------------------------------------------------


class TestMediaKeySafety:
    """The only code here that mutates SYSTEM-WIDE state. Previously untested."""

    def test_restore_is_a_noop_when_suppression_never_ran(self, monkeypatch):
        """Regression: atexit fires on bare import, so `pytest` itself was
        clearing the developer's system-wide UserKeyMapping on every run."""
        calls = []
        monkeypatch.setattr(lg.subprocess, "run", lambda *a, **k: calls.append(a))
        monkeypatch.setattr(lg, "_MEDIA_KEYS_SUPPRESSED", False)
        lg._restore_media_keys()
        assert calls == [], "restore must not touch hidutil when we never suppressed"

    def test_suppress_refuses_when_user_has_own_mappings(self, monkeypatch, capsys):
        """We replace the whole mapping array, so suppressing on top of a
        user's Caps-Lock remap would destroy it irrecoverably."""
        if lg.platform.system() != "Darwin":
            pytest.skip("macOS-only path")
        monkeypatch.setattr(lg, "_user_has_existing_key_mappings", lambda: True)
        calls = []
        monkeypatch.setattr(lg.subprocess, "run", lambda *a, **k: calls.append(a))
        monkeypatch.setattr(lg, "_MEDIA_KEYS_SUPPRESSED", False)
        lg._suppress_media_keys()
        assert calls == [], "must not overwrite pre-existing user key mappings"
        assert "NOT be suppressed" in capsys.readouterr().out

    def test_existing_mapping_probe_fails_safe(self, monkeypatch):
        """If we cannot tell what the user has, assume they have something."""

        def boom(*a, **k):
            raise OSError("hidutil missing")

        monkeypatch.setattr(lg.subprocess, "run", boom)
        assert lg._user_has_existing_key_mappings() is True


class TestAudioDeviceFailure:
    def test_dead_output_device_does_not_crash(self, monkeypatch, capsys):
        """Regression: SOUND_AVAILABLE only means the libraries IMPORTED.
        A missing output device raised PortAudioError out of play_random_tone
        and out of main()'s event loop, killing the game on the first keypress.
        README promises a visual-only fallback for exactly this case."""
        if not lg.SOUND_AVAILABLE:
            pytest.skip("audio stack unavailable")
        import sounddevice as sd

        def boom(*a, **k):
            raise sd.PortAudioError("Device unavailable")

        monkeypatch.setattr(sd, "play", boom)
        lg.play_random_tone()  # must not raise
        assert "audio unavailable" in capsys.readouterr().out


class TestKeyNameSentinel:
    def test_unknown_is_rejected(self):
        """pygame.K_UNKNOWN is 0 and is the one K_* that is not a real key.
        It passed the isinstance(int) guard, so {"key": "UNKNOWN"} produced a
        shortcut no keystroke could match -- locking the parent out."""
        assert pygame.K_UNKNOWN == 0
        key, resolved = lg.resolve_key_name("UNKNOWN")
        assert resolved is None, "K_UNKNOWN must not count as resolved"
        assert key == pygame.K_ESCAPE

    def test_unknown_config_still_leaves_a_working_exit(self, shortcut, mods):
        cfg = shortcut("UNKNOWN", ctrl=True, shift=True)
        assert lg.get_exit_shortcut_display(cfg) == "Ctrl+Shift+Esc"
        mods(CTRL_SHIFT)
        assert lg.check_exit_shortcut(keydown(pygame.K_ESCAPE), cfg)


class TestDisplaySiblingHardening:
    @pytest.mark.parametrize(
        "cfg",
        [
            {"exit_shortcut": "hello"},
            {"exit_shortcut": [1, 2]},
            {"exit_shortcut": 5},
            {"exit_shortcut": None},
        ],
    )
    def test_non_dict_shortcut_does_not_raise(self, cfg):
        """check_exit_shortcut was hardened against these; its sibling
        get_exit_shortcut_display was not, and raised AttributeError."""
        assert lg.get_exit_shortcut_display(cfg) == "Ctrl+Shift+Esc"


class TestConfigPreservation:
    @pytest.fixture(autouse=True)
    def _isolate(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lg, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(lg, "CONFIG_FILE", tmp_path / "config.json")
        self.tmp = tmp_path
        self.cfg = tmp_path / "config.json"

    def test_non_utf8_config_does_not_crash(self):
        """Regression: UnicodeDecodeError is a ValueError, NOT a
        JSONDecodeError, so it escaped the except clause and crashed the game
        at import. write_text() cannot express this input -- which is exactly
        why the original 8 regression cases could not catch it."""
        self.cfg.write_bytes(b'{"exit_shortcut": {"key": "\xff\xfe"}}')
        assert lg.load_config() == lg.DEFAULT_CONFIG

    def test_rejected_config_is_preserved_not_destroyed(self):
        """A parent who mistypes one field must not lose their file."""
        original = '{"_note": "Dad set F10", "exit_shortcut": {"key": "F10", "ctrl": true, "shift": true, "alt": "false"}}'
        self.cfg.write_text(original)
        lg.load_config()
        backup = self.cfg.with_suffix(".json.rejected")
        assert backup.exists(), "the rejected config must be kept, not deleted"
        assert backup.read_text() == original, "backup must be byte-identical"

    def test_first_run_says_created_not_replaced(self, capsys):
        assert not self.cfg.exists()
        lg.load_config()
        assert "Created config file" in capsys.readouterr().out

    def test_replacing_says_replaced(self, capsys):
        self.cfg.write_text("{ broken")
        lg.load_config()
        assert "Replaced config file" in capsys.readouterr().out


class TestConfigGuardsAreIndependentlyDetected:
    """Regression for an OVERDETERMINED test: the original suite passed with
    either half of the 0e2f2b0 fix reverted, so neither half was verified.
    These assert on the two paths separately, by their distinct output."""

    @pytest.fixture(autouse=True)
    def _isolate(self, tmp_path, monkeypatch):
        monkeypatch.setattr(lg, "CONFIG_DIR", tmp_path)
        monkeypatch.setattr(lg, "CONFIG_FILE", tmp_path / "config.json")
        self.cfg = tmp_path / "config.json"

    def test_isinstance_guard_path_rejects_without_raising(self, capsys):
        """A non-dict exit_shortcut must be caught by the isinstance guard
        (structure message), NOT by the except clause (error message)."""
        self.cfg.write_text('{"exit_shortcut": "hello"}')
        assert lg.load_config() == lg.DEFAULT_CONFIG
        out = capsys.readouterr().out
        assert (
            "Invalid config structure" in out
        ), "must be rejected by the isinstance guard, not by the except clause"
        assert "Error loading config file" not in out

    @pytest.mark.parametrize("content", ["5", "null", "true", '"hello"'])
    def test_root_isinstance_guard_rejects_non_dict_roots(self, content, capsys):
        """The ROOT guard, separately from the exit_shortcut guard.

        Without `isinstance(config, dict)`, a scalar root reaches
        `"exit_shortcut" in config`, which raises TypeError and is only mopped
        up by the except clause -- so the two guards become interchangeable and
        neither is verified. Asserting on WHICH message appears keeps them
        independently falsifiable.
        """
        self.cfg.write_text(content)
        assert lg.load_config() == lg.DEFAULT_CONFIG
        out = capsys.readouterr().out
        assert (
            "Invalid config structure" in out
        ), "a non-dict root must be rejected by the isinstance guard"
        assert "Error loading config file" not in out, (
            "must not reach the except clause -- that would mean the root "
            "guard is absent and the except clause is masking it"
        )

    def test_except_clause_path_catches_decode_errors(self, capsys):
        """Non-UTF-8 bytes cannot be caught by an isinstance guard -- only the
        widened except clause can. Distinct message proves which fired."""
        self.cfg.write_bytes(b"\xff\xfe\x00bad")
        assert lg.load_config() == lg.DEFAULT_CONFIG
        assert "Error loading config file" in capsys.readouterr().out
