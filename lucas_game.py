#!/Users/warnes/src/lucas_game/venv/bin/python
"""
Lucas' Game - interactive color and sound keyboard game for children.
Shows a fullscreen title screen, displays pressed keys, and supports a configurable exit shortcut.

Copyright (c) 2025 Gregory R. Warnes
License: MIT
"""

import atexit
import json
import os
import platform
import random
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import pygame
from platformdirs import user_config_dir

# Initialize Pygame
pygame.init()

# Initialize font module
try:
    pygame.font.init()
except Exception as e:
    print(f"Warning: Font initialization issue: {e}")

# Try to initialize sound, but continue if not available
SOUND_AVAILABLE = False
SOUND_ERROR = ""
try:
    import numpy as np
    import sounddevice as sd

    SOUND_AVAILABLE = True
except (ImportError, NotImplementedError, OSError) as e:
    # Recorded so the title screen can report it: when launched from the macOS
    # Dock there is no console, so a stderr message alone is invisible.
    SOUND_ERROR = str(e)
    print(f"Sound not available: {e}")
    print("Continuing without sound support.")

# ---------------------------------------------------------------------------
# Media key suppression (macOS / Touch Bar)
# ---------------------------------------------------------------------------
# On macOS, remap system media and brightness keys to F13 via hidutil so the
# child cannot accidentally change volume, brightness, or media playback.
# The Touch Bar emits the same HID events as physical media keys, so this
# suppresses Smart Bar presses too.  Our own suppression is undone on exit
# (normal, crash, or SIGTERM).  Note this is NOT a save/restore: hidutil has one
# system-wide mapping list and setting it replaces the whole thing, so we cannot
# add to a user's existing mappings without losing them.  Rather than destroy
# them, _suppress_media_keys() skips entirely when the user already has any.

# Consumer-page (0x0C) HID usage codes for keys to suppress.
# Format: (usagePage << 32) | usage
_MACOS_MEDIA_HID_SRCS = [
    0xC0000006F,  # Display Brightness Increment
    0xC00000070,  # Display Brightness Decrement
    0xC000000B3,  # Fast Forward
    0xC000000B4,  # Rewind
    0xC000000B5,  # Scan Next Track
    0xC000000B6,  # Scan Previous Track
    0xC000000B7,  # Stop
    0xC000000B8,  # Eject
    0xC000000CD,  # Play/Pause
    0xC000000E2,  # Mute
    0xC000000E9,  # Volume Increment
    0xC000000EA,  # Volume Decrement
]
# Destination: F13 on Keyboard page (0x07), usage 0x68.
# F13 is ignored by the game's event loop, so the press becomes a no-op.
_MACOS_MEDIA_HID_DST = 0x700000068


# Set only after a suppression actually succeeds.  The restore path is a
# system-wide mutation, so it must never run on the strength of "this module was
# imported" -- see _restore_media_keys().
_MEDIA_KEYS_SUPPRESSED = False


def _user_has_existing_key_mappings():
    """True if the user already has their own hidutil UserKeyMapping entries.

    We replace the whole mapping array, so suppressing on top of someone's
    Caps-Lock-to-Escape remap would destroy it with no way to put it back.
    On any doubt (command missing, unreadable output) report True and skip
    suppression: failing to protect the media keys is recoverable, silently
    eating a user's keyboard configuration is not.
    """
    try:
        result = subprocess.run(
            ["hidutil", "property", "--get", "UserKeyMapping"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:  # noqa: BLE001 - fail safe, see docstring
        return True
    return "HIDKeyboardModifierMappingSrc" in result.stdout


def _suppress_media_keys():
    """Remap system media/brightness keys to F13 via hidutil (macOS only)."""
    global _MEDIA_KEYS_SUPPRESSED
    if platform.system() != "Darwin":
        return
    if _user_has_existing_key_mappings():
        print(
            "Note: you already have custom keyboard mappings (hidutil), so media "
            "keys will NOT be suppressed -- overwriting them would destroy your "
            "configuration with no way to restore it."
        )
        return
    mapping = json.dumps(
        {
            "UserKeyMapping": [
                {
                    "HIDKeyboardModifierMappingSrc": src,
                    "HIDKeyboardModifierMappingDst": _MACOS_MEDIA_HID_DST,
                }
                for src in _MACOS_MEDIA_HID_SRCS
            ]
        }
    )
    try:
        subprocess.run(
            ["hidutil", "property", "--set", mapping],
            check=True,
            capture_output=True,
        )
        _MEDIA_KEYS_SUPPRESSED = True
    except Exception as e:  # noqa: BLE001 - sibling of _restore_media_keys
        # Broad for the same reason the restore path is: this is a convenience
        # feature called on the way into the game, and no failure of it is worth
        # taking the game down for.  The narrow (CalledProcessError,
        # FileNotFoundError) pair missed PermissionError and every other OSError,
        # any of which crashed the game at startup before the title screen.
        print(f"Warning: Could not suppress media keys: {e}")


def _restore_media_keys():
    """Undo our own media-key suppression (macOS only).

    Guarded on _MEDIA_KEYS_SUPPRESSED, and that guard is load-bearing: this
    function is registered with atexit at module scope, so without it MERELY
    IMPORTING this module -- which `pytest` does at collection -- would clear
    the user's system-wide UserKeyMapping at interpreter exit, having never
    started the game or set anything.
    """
    global _MEDIA_KEYS_SUPPRESSED
    if not _MEDIA_KEYS_SUPPRESSED or platform.system() != "Darwin":
        return
    try:
        subprocess.run(
            ["hidutil", "property", "--set", '{"UserKeyMapping": []}'],
            check=True,
            capture_output=True,
        )
    except Exception as e:  # noqa: BLE001 - see rationale below
        # Deliberately broad.  This is the teardown path: it runs from atexit
        # and from the SIGTERM handler, and anything it lets escape leaves the
        # user's media and brightness keys remapped to F13 SYSTEM-WIDE, with no
        # obvious way to undo it.  Failing to restore is bad; failing to
        # restore *and* raising out of an exit handler is worse.
        print(f"Warning: Could not restore media keys: {e}")
        print("Reset manually with: hidutil property --set '{\"UserKeyMapping\":[]}'")
    finally:
        _MEDIA_KEYS_SUPPRESSED = False


atexit.register(_restore_media_keys)


def _sigterm_handler(signum, frame):
    """Restore media keys and exit on SIGTERM.

    Exits 143 (128 + SIGTERM), NOT 0.  pi_setup.sh's kiosk loop treats exit 0 as
    "the parent pressed the exit shortcut" and stops restarting; a stray SIGTERM
    returning 0 would therefore break out of the loop and leave an autologin
    shell with passwordless sudo on screen in front of the child.  Zero is
    reserved for the deliberate exit-shortcut path.
    """
    _restore_media_keys()
    pygame.quit()
    sys.exit(143)


signal.signal(signal.SIGTERM, _sigterm_handler)

# Set of pygame key codes to silently ignore in the event loop.
# Media keys are remapped to F13 by _suppress_media_keys(); swallowing them
# here provides defense-in-depth and prevents spurious color/sound changes.
_IGNORED_KEYS = frozenset({pygame.K_F13})

# ---------------------------------------------------------------------------

# Set up fullscreen display
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Random Color Screen")

# Get screen dimensions
width, height = screen.get_size()

# Configuration file path (OS-appropriate location using platformdirs)
CONFIG_DIR = Path(user_config_dir("lucas-game", "warnes"))
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default configuration
DEFAULT_CONFIG = {
    "exit_shortcut": {"key": "ESCAPE", "ctrl": True, "shift": True, "alt": False}
}


def load_config():
    """Load configuration from file or create default config."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            # Validate required keys and structure.  Check the CONTAINER types
            # explicitly: a config of {"exit_shortcut": "hello"} would otherwise
            # reach .get() on a str and raise AttributeError, and a config whose
            # root is a bare scalar would raise TypeError on the `in` test.
            # Neither is caught below, and load_config() runs at import time --
            # so a malformed file crashed the game before the title screen.
            if isinstance(config, dict) and isinstance(
                config.get("exit_shortcut"), dict
            ):
                shortcut = config["exit_shortcut"]
                # Check that all required fields exist and have correct types
                if (
                    isinstance(shortcut.get("key"), str)
                    and len(shortcut.get("key", "")) > 0
                    and isinstance(shortcut.get("ctrl"), bool)
                    and isinstance(shortcut.get("shift"), bool)
                    and isinstance(shortcut.get("alt"), bool)
                ):
                    return config
                print("Warning: Invalid config structure, using defaults")
            else:
                print("Warning: Invalid config structure, using defaults")
        except (ValueError, OSError, AttributeError, TypeError) as e:
            # ValueError (not JSONDecodeError) because a config saved in another
            # encoding raises UnicodeDecodeError, which is a ValueError and is
            # NOT a JSONDecodeError -- that gap crashed the game at import.
            # OSError covers IOError.  This function must never propagate: it is
            # called at module scope, before any UI exists to report the failure.
            print(f"Warning: Error loading config file: {e}")

    # Preserve anything we are about to replace.  Reaching here with an existing
    # file means we rejected the user's own content, and overwriting it destroys
    # a hand-edited shortcut with no way to get it back -- on a kiosk, where the
    # warning above goes to a console nobody reads.
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Warning: Could not create config directory: {e}")
        return DEFAULT_CONFIG

    replacing = CONFIG_FILE.exists()
    if replacing:
        backup = CONFIG_FILE.with_suffix(".json.rejected")
        try:
            shutil.copy2(CONFIG_FILE, backup)
            print(f"Your previous config was kept at: {backup}")
        except OSError as e:
            print(f"Warning: could not back up existing config, not replacing it: {e}")
            return DEFAULT_CONFIG

    # Write atomically: a truncating write that is interrupted (a child pulling
    # the plug on a kiosk) leaves a partial file that the next run also rejects.
    try:
        tmp_path = CONFIG_FILE.with_suffix(".json.tmp")
        with open(tmp_path, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        os.replace(tmp_path, CONFIG_FILE)
        print(f"{'Replaced' if replacing else 'Created'} config file at: {CONFIG_FILE}")
    except OSError as e:
        print(f"Warning: Could not write config file: {e}")

    return DEFAULT_CONFIG


_KEY_RESOLUTION_WARNED = set()


def resolve_key_name(name):
    """Resolve a config key name to a pygame key constant.

    Returns ``(key_constant, resolved_name)``.  ``resolved_name`` is the
    config spelling that actually worked, or ``None`` when the name could not
    be resolved at all -- in which case the caller falls back to ESCAPE.

    pygame's key constants are inconsistently cased: letters are lowercase
    (``K_q``) while everything else is uppercase (``K_ESCAPE``, ``K_F10``,
    ``K_RETURN``).  Accepting either case for letters keeps a natural-looking
    ``"key": "Q"`` working instead of silently degrading to ESCAPE.
    """
    if not isinstance(name, str) or not name:
        return pygame.K_ESCAPE, None

    for candidate in (name, name.lower(), name.upper()):
        key = getattr(pygame, f"K_{candidate}", None)
        # `!= K_UNKNOWN` is load-bearing, not defensive noise.  pygame.K_UNKNOWN
        # is 0 and is the one K_* constant that is not a real key, so a config of
        # {"key": "UNKNOWN"} passes an isinstance(int) check, resolves happily,
        # and produces a shortcut NO KEYSTROKE CAN MATCH -- the hint would read
        # "Ctrl+Shift+Unknown" while the parent has no way out at all.
        if isinstance(key, int) and key != pygame.K_UNKNOWN:
            return key, candidate

    # Unresolvable: fall back to ESCAPE, but say so.  A silent fallback makes
    # the on-screen hint disagree with the shortcut that actually exits.
    if name not in _KEY_RESOLUTION_WARNED:
        _KEY_RESOLUTION_WARNED.add(name)
        print(
            f"Warning: unknown exit-shortcut key {name!r}; falling back to ESCAPE. "
            "Use a pygame key name without the 'K_' prefix (e.g. ESCAPE, Q, F10)."
        )
    return pygame.K_ESCAPE, None


def get_exit_shortcut_display(config):
    """Get a human-readable display string for the exit shortcut."""
    try:
        # Same hardening as check_exit_shortcut(): keep `shortcut` a dict
        # whatever the config held, or the .get() calls below raise
        # AttributeError, which the except clause does not catch.  This function
        # is called from the title screen, the hint, and main().
        candidate = config["exit_shortcut"]
        shortcut = (
            candidate
            if isinstance(candidate, dict)
            else DEFAULT_CONFIG["exit_shortcut"]
        )
        parts = []

        if shortcut.get("ctrl", False):
            parts.append("Ctrl")
        if shortcut.get("shift", False):
            parts.append("Shift")
        if shortcut.get("alt", False):
            parts.append("Alt")

        # Show the key that will ACTUALLY exit, not the one that was asked
        # for: an unresolvable name falls back to ESCAPE, and a hint that
        # advertises the wrong key is worse than no hint at all.
        _, resolved = resolve_key_name(shortcut["key"])
        key = resolved if resolved is not None else "ESCAPE"
        key_display = "Esc" if key.upper() == "ESCAPE" else key.title()
        parts.append(key_display)

        return "+".join(parts)
    except (KeyError, TypeError):
        # Fallback to default if config is malformed
        return "Ctrl+Shift+Esc"


def check_exit_shortcut(event, config):
    """Check if the event matches the configured exit shortcut."""
    # Bind up front: if the lookup below fails, the modifier checks further
    # down still reference `shortcut`, and an unbound name raises NameError --
    # which is NOT caught by their `except (KeyError, TypeError)`.
    shortcut = DEFAULT_CONFIG["exit_shortcut"]
    try:
        candidate = config["exit_shortcut"]
        # Keep `shortcut` a dict no matter what the config held, so the
        # .get() calls below cannot raise AttributeError either.
        if isinstance(candidate, dict):
            shortcut = candidate

        # Get the key constant from pygame (case-tolerant for letter keys)
        expected_key, _ = resolve_key_name(shortcut["key"])
    except (KeyError, TypeError, AttributeError):
        # Fallback to default ESC if config is malformed
        expected_key = pygame.K_ESCAPE

    # Check if the key matches
    if event.key != expected_key:
        return False

    try:
        # Get modifier states
        mods = pygame.key.get_mods()

        # Check ctrl
        ctrl_pressed = bool(mods & pygame.KMOD_CTRL)
        if shortcut.get("ctrl", False) != ctrl_pressed:
            return False

        # Check shift
        shift_pressed = bool(mods & pygame.KMOD_SHIFT)
        if shortcut.get("shift", False) != shift_pressed:
            return False

        # Check alt
        alt_pressed = bool(mods & pygame.KMOD_ALT)
        if shortcut.get("alt", False) != alt_pressed:
            return False

        return True
    except (KeyError, TypeError):
        # If we can't get modifiers from config, just check the key
        return event.key == expected_key


# Load configuration
config = load_config()


def generate_random_color():
    """Generate a random RGB color."""
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def show_title_screen(screen, config):
    """Display title screen and instructions."""
    screen_width, screen_height = screen.get_size()
    screen.fill((20, 20, 40))  # Dark blue background

    # Title
    title_font = pygame.font.Font(None, 120)
    title_text = title_font.render("Lucas' Game", True, (255, 200, 50))
    title_x = (screen_width - title_text.get_width()) // 2
    title_y = screen_height // 6
    screen.blit(title_text, (title_x, title_y))

    # Instructions
    instruction_font = pygame.font.Font(None, 48)
    exit_shortcut = get_exit_shortcut_display(config)
    instructions = [
        "Press any key to see it displayed",
        "with a random color and sound!",
        "",
        f"Press {exit_shortcut} to exit",
        "",
        "Press any key to start...",
    ]

    y_offset = screen_height // 2.5
    for instruction in instructions:
        text = instruction_font.render(instruction, True, (200, 200, 200))
        x = (screen_width - text.get_width()) // 2
        screen.blit(text, (x, y_offset))
        y_offset += 60

    # Warn on screen if sound failed to initialize
    if not SOUND_AVAILABLE:
        warning_font = pygame.font.Font(None, 32)
        for line in ("Sound is not available:", SOUND_ERROR):
            warning = warning_font.render(line, True, (255, 120, 120))
            screen.blit(warning, ((screen_width - warning.get_width()) // 2, y_offset))
            y_offset += 36

    # Copyright
    copyright_font = pygame.font.Font(None, 32)
    copyright_text = copyright_font.render(
        "© 2025 Gregory R. Warnes", True, (150, 150, 150)
    )
    copyright_x = (screen_width - copyright_text.get_width()) // 2
    copyright_y = screen_height - 60
    screen.blit(copyright_text, (copyright_x, copyright_y))

    pygame.display.flip()

    # Wait for any key press
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if check_exit_shortcut(event, config):
                    return None
                if event.key in _IGNORED_KEYS:
                    continue  # Silently ignore remapped media keys
                return event  # Return the key event
    return None


def get_key_name(key):
    """Convert pygame key constant to a display name."""
    # Handle letter keys
    if pygame.K_a <= key <= pygame.K_z:
        return chr(key).upper()

    # Handle number keys
    if pygame.K_0 <= key <= pygame.K_9:
        return chr(key)

    # Handle special keys with custom names
    key_names = {
        pygame.K_SPACE: "Space",
        pygame.K_RETURN: "Return",
        pygame.K_BACKSPACE: "Backspace",
        pygame.K_TAB: "Tab",
        pygame.K_DELETE: "Delete",
        pygame.K_UP: "↑",
        pygame.K_DOWN: "↓",
        pygame.K_LEFT: "←",
        pygame.K_RIGHT: "→",
        pygame.K_LSHIFT: "Shift",
        pygame.K_RSHIFT: "Shift",
        pygame.K_LCTRL: "Ctrl",
        pygame.K_RCTRL: "Ctrl",
        pygame.K_LALT: "Alt",
        pygame.K_RALT: "Alt",
        pygame.K_LSUPER: "Command",
        pygame.K_RSUPER: "Command",
        pygame.K_LMETA: "Meta",
        pygame.K_RMETA: "Meta",
        pygame.K_CAPSLOCK: "Caps Lock",
        pygame.K_MODE: "Mode",
        pygame.K_COMMA: ",",
        pygame.K_PERIOD: ".",
        pygame.K_SLASH: "/",
        pygame.K_SEMICOLON: ";",
        pygame.K_QUOTE: "'",
        pygame.K_LEFTBRACKET: "[",
        pygame.K_RIGHTBRACKET: "]",
        pygame.K_BACKSLASH: "\\",
        pygame.K_MINUS: "-",
        pygame.K_EQUALS: "=",
        pygame.K_BACKQUOTE: "`",
        # Function keys
        pygame.K_F1: "F1",
        pygame.K_F2: "F2",
        pygame.K_F3: "F3",
        pygame.K_F4: "F4",
        pygame.K_F5: "F5",
        pygame.K_F6: "F6",
        pygame.K_F7: "F7",
        pygame.K_F8: "F8",
        pygame.K_F9: "F9",
        pygame.K_F10: "F10",
        pygame.K_F11: "F11",
        pygame.K_F12: "F12",
        pygame.K_F13: "F13",
        pygame.K_F14: "F14",
        pygame.K_F15: "F15",
        # Navigation keys
        pygame.K_HOME: "Home",
        pygame.K_END: "End",
        pygame.K_PAGEUP: "Page Up",
        pygame.K_PAGEDOWN: "Page Down",
        pygame.K_INSERT: "Insert",
    }

    # Use pygame's name as fallback, cleaned up
    return key_names.get(key, pygame.key.name(key).title())


def draw_key(screen, key_name, color, text_color=(255, 255, 255)):
    """Draw a key-shaped box with the key name filling 75% of the display."""
    screen_width, screen_height = screen.get_size()

    # Calculate key dimensions (75% of screen)
    key_width = int(screen_width * 0.75)
    key_height = int(screen_height * 0.75)

    # Center position
    key_x = (screen_width - key_width) // 2
    key_y = (screen_height - key_height) // 2

    # Draw rounded rectangle for key background
    key_rect = pygame.Rect(key_x, key_y, key_width, key_height)
    border_radius = min(key_width, key_height) // 10

    # Draw key shadow (darker version of color)
    shadow_offset = 10
    shadow_color = tuple(max(0, c - 50) for c in color)
    shadow_rect = pygame.Rect(
        key_x + shadow_offset, key_y + shadow_offset, key_width, key_height
    )
    pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=border_radius)

    # Draw key body
    pygame.draw.rect(screen, color, key_rect, border_radius=border_radius)

    # Draw key border
    border_color = tuple(min(255, c + 50) for c in color)
    pygame.draw.rect(
        screen, border_color, key_rect, width=5, border_radius=border_radius
    )

    # Calculate font size to fit the text
    font_size = int(key_height * 0.6)
    font = pygame.font.Font(None, font_size)

    # Adjust font size if text is too wide
    text_surface = font.render(key_name, True, text_color)
    while text_surface.get_width() > key_width * 0.9 and font_size > 20:
        font_size -= 10
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(key_name, True, text_color)

    # Center the text
    text_x = key_x + (key_width - text_surface.get_width()) // 2
    text_y = key_y + (key_height - text_surface.get_height()) // 2

    screen.blit(text_surface, (text_x, text_y))


def draw_exit_hint(screen, config):
    """Draw a small hint in the corner showing the exit shortcut."""
    screen_width, screen_height = screen.get_size()

    # Create semi-transparent background for better readability
    hint_font = pygame.font.Font(None, 28)
    exit_shortcut = get_exit_shortcut_display(config)
    hint_text = f"Exit: {exit_shortcut}"

    # Render text
    text_surface = hint_font.render(hint_text, True, (255, 255, 255))

    # Calculate position (bottom-right corner with padding)
    padding = 15
    text_x = screen_width - text_surface.get_width() - padding
    text_y = screen_height - text_surface.get_height() - padding

    # Draw semi-transparent background
    bg_padding = 8
    bg_rect = pygame.Rect(
        text_x - bg_padding,
        text_y - bg_padding,
        text_surface.get_width() + bg_padding * 2,
        text_surface.get_height() + bg_padding * 2,
    )

    # Create a surface for the background with alpha
    bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
    bg_surface.set_alpha(128)  # 50% transparency
    bg_surface.fill((0, 0, 0))
    screen.blit(bg_surface, (bg_rect.x, bg_rect.y))

    # Draw text
    screen.blit(text_surface, (text_x, text_y))


def generate_tone(frequency, duration=0.2, sample_rate=22050):
    """Generate a tone with the given frequency and duration."""
    if not SOUND_AVAILABLE:
        return None

    import numpy as np

    num_samples = int(duration * sample_rate)
    # Create a sine wave
    t = np.linspace(0, duration, num_samples, False)
    tone = np.sin(2 * np.pi * frequency * t)

    # Apply fade in/out to avoid clicks
    fade_samples = int(0.01 * sample_rate)  # 10ms fade
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    tone[:fade_samples] *= fade_in
    tone[-fade_samples:] *= fade_out

    # Convert to 16-bit integer format
    tone = (tone * 32767).astype(np.int16)

    return tone


def play_random_tone():
    """Play a random musical tone."""
    if not SOUND_AVAILABLE:
        # Visual feedback when sound is not available
        print("♪")
        return

    # Generate a random frequency between 200 Hz and 1000 Hz
    # Using musical notes for better sound
    frequencies = [
        261.63,
        293.66,
        329.63,
        349.23,
        392.00,
        440.00,
        493.88,
        523.25,
    ]  # C, D, E, F, G, A, B, C
    frequency = random.choice(frequencies)

    tone = generate_tone(frequency, duration=1.0)
    if tone is not None:
        import sounddevice as sd

        # Convert to float32 for sounddevice (range -1.0 to 1.0)
        tone_float = tone.astype(np.float32) / 32767.0
        try:
            sd.play(tone_float, 22050)
            sd.wait()  # Wait for the tone to finish playing
        except Exception as e:  # noqa: BLE001 - see below
            # SOUND_AVAILABLE only means numpy and sounddevice IMPORTED; it says
            # nothing about a working output device.  A headless Pi, a VM, or a
            # Mac with no output raises PortAudioError here, and neither this
            # function nor main()'s event loop caught it -- so the game died on
            # the first keypress.  Degrade to the visual-only mode the README
            # already promises for "audio libraries or audio devices".
            print(f"♪ (audio unavailable: {e})")


def main():
    """Main game loop."""
    _suppress_media_keys()
    clock = pygame.time.Clock()

    # Show title screen and get the starting key event
    start_event = show_title_screen(screen, config)
    if start_event is None:
        pygame.quit()
        return

    running = True

    # Use the title screen key press for the first action
    current_color = generate_random_color()
    screen.fill(current_color)
    key_name = get_key_name(start_event.key)
    draw_key(screen, key_name, current_color)
    draw_exit_hint(screen, config)
    pygame.display.flip()

    exit_shortcut = get_exit_shortcut_display(config)
    print("Random Color Screen")
    print("Press any key to change color and play a tone")
    print(f"Press {exit_shortcut} to exit")
    if not SOUND_AVAILABLE:
        print("\nNote: Sound is not available on this system")
        print("Visual feedback (♪) will be shown instead")

    # Play tone for the first key press
    play_random_tone()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if check_exit_shortcut(event, config):
                    running = False
                elif event.key in _IGNORED_KEYS:
                    pass  # Silently ignore remapped media keys
                else:
                    # Change color and play tone
                    current_color = generate_random_color()
                    screen.fill(current_color)

                    # Get the key name and draw it
                    key_name = get_key_name(event.key)
                    draw_key(screen, key_name, current_color)

                    # Draw exit hint in corner
                    draw_exit_hint(screen, config)

                    pygame.display.flip()
                    play_random_tone()
                    # Clear any keystrokes that happened during tone playback
                    pygame.event.clear(pygame.KEYDOWN)

        clock.tick(60)  # 60 FPS

    pygame.quit()


if __name__ == "__main__":
    main()
