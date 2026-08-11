# Lucas' Game - AI Agent Instructions

## Project Overview

**Lucas' Game** is a fullscreen interactive application for young children that displays random colors and plays musical tones when keys are pressed. It targets multiple platforms with deployment-specific build requirements.

**Key Insight**: This is NOT a traditional app—it's designed as a kiosk application that runs unattended. Exit shortcuts are intentionally complex (Ctrl+Shift+Esc) to prevent accidental exits by children.

## Architecture & Critical Files

### Entry Point & Main Logic
- **`lucas_game.py`** - Single-file application (~470 lines)
- Gracefully degrades if sound libraries unavailable (pygame + numpy + sounddevice)
- Uses `platformdirs` for OS-appropriate config paths (NOT hardcoded `~/.config`)

### Platform-Specific Build System

**macOS Application Bundle** (`setup.py` + `build_macos.sh`):
- Uses `py2app` to create standalone `.app` bundle
- **CRITICAL**: `setup.py` APP list must match actual filename (`lucas_game.py`)
- **CRITICAL**: `setup.py` packages list must match `requirements.txt`
- Icon generation via pygame (`create_icon.py`) → macOS iconset → `.icns`
- Build must be from activated venv: `source venv/bin/activate`

**Raspberry Pi Kiosk** (`pi_setup.sh` + `RASPBERRY_PI_SETUP.md`):
- Builds pygame from source (no binary wheels): `pip install pygame --no-binary :all:`
- Auto-login + auto-start via `.bashrc` modification
- Uses SDL2 system libraries (must install libsdl2-* packages)
- **Target**: Console boot (no X11/Wayland), direct framebuffer

## Build Script Synchronization

**⚠️ CRITICAL PATTERN**: When renaming files or changing dependencies, you MUST update ALL build configurations:

```python
# If you rename lucas_game.py → something_else.py, update:
setup.py:    APP = ['something_else.py']  # Not just lucas_game.py!

# If you add package to requirements.txt, update:
setup.py:    'packages': [..., 'new_package']

# If you change filename in code, update:
pi_setup.sh:         python lucas_game.py     # Line 71
pi_setup.sh:         echo "...lucas_game.py..." # Line 105, 112
RASPBERRY_PI_SETUP.md: All references in code blocks
README.md:          ./lucas_game.py           # Usage section
```

**Why**: Build scripts hardcode filenames—they don't auto-discover. Stale references cause silent failures in packaged apps.

## Configuration System

**Config file location** (uses `platformdirs.user_config_dir`):
- macOS: `~/Library/Application Support/lucas-game/config.json`
- Linux: `~/.config/lucas-game/config.json`
- Windows: `%APPDATA%\lucas-game\config.json`

**Exit shortcut configuration**:
```json
{
  "exit_shortcut": {
    "key": "ESCAPE",      // Pygame constant name WITHOUT K_ prefix
    "ctrl": true,         // Boolean, not string
    "shift": true,
    "alt": false
  }
}
```

**Key validation** (`load_config()` in `lucas_game.py`): Config loader validates types. Invalid config falls back to defaults, creating new config file.

## Dependencies & Platform Quirks

### pygame Font/Mixer Issue (macOS)
**Problem**: macOS pygame binary wheels often lack SDL2 font/mixer support  
**Solution**: Build from source after installing SDL2 via Homebrew:
```bash
brew install sdl2 sdl2_mixer sdl2_ttf sdl2_image
pip cache remove pygame
pip install pygame --no-binary :all:
```

### Sound Availability Pattern
```python
SOUND_AVAILABLE = False
try:
    import numpy as np
    import sounddevice as sd
    SOUND_AVAILABLE = True
except (ImportError, NotImplementedError, OSError) as e:
    print(f"Sound not available: {e}")
    # Continue without sound - visual-only mode
```
**Why**: Headless systems (Docker, some Linux servers) lack audio devices. App must function without sound.

### py2app Must Not Zip `_sounddevice_data`
**Problem**: The `.app` runs silently — sound works via `python lucas_game.py` but not when launched from the Dock.
**Cause**: py2app zips pure-Python packages into `Resources/lib/python39.zip`. `sounddevice` locates
`libportaudio.dylib` through `_sounddevice_data.__path__`, and `dlopen()` cannot read a dylib from inside a
zip (`OSError ... errno=20`). That `OSError` is swallowed by the `SOUND_AVAILABLE` guard, so the app degrades
to silent mode with no visible error — stderr goes nowhere when launched from the Dock.
**Solution**: List `_sounddevice_data` (and `cffi`) in `OPTIONS["packages"]` in `setup.py`; py2app then copies
them as real directory trees. Verify after building:
```bash
ls "dist/Lucas' Game.app/Contents/Resources/lib/python3.9/_sounddevice_data/portaudio-binaries/"
```
The title screen also displays the `SOUND_ERROR` text whenever sound fails, so this class of bug is visible
without a console.

### Sound Playback Blocks the Event Loop
`play_random_tone()` calls `sd.wait()`, which **blocks the main thread for the full tone duration (1 second)**. To prevent key-press accumulation during that block, `pygame.event.clear(pygame.KEYDOWN)` is called immediately after. Any change to audio timing must account for this: adding async audio would require removing the `event.clear()` call or replacing it with smarter debouncing.

## Testing Workflows

### Development Testing
```bash
source venv/bin/activate
python lucas_game.py
# Exit with configured shortcut (default: Ctrl+Shift+Esc)
```

### macOS Build Testing
```bash
./build_macos.sh
open "dist/Lucas' Game.app"
```

### Raspberry Pi Testing
```bash
ssh pi@raspberrypi.local
cd ~/lucas_game
source venv/bin/activate
python lucas_game.py
```

## Anti-Patterns & Common Errors

❌ **DON'T** run `./lucas_game.py` directly—the shebang is hardcoded to a specific user's venv path  
✅ **DO** use `python lucas_game.py` from the activated venv

❌ **DON'T** use `pip install pygame` on macOS without checking SDL2 support  
✅ **DO** build from source with SDL2 libraries installed

❌ **DON'T** hardcode config paths like `~/.config/lucas-game`  
✅ **DO** use `platformdirs.user_config_dir("lucas-game", "warnes")`

❌ **DON'T** assume sound is available  
✅ **DO** check `SOUND_AVAILABLE` flag before calling sound functions

❌ **DON'T** rename files without updating setup.py, build scripts, and docs  
✅ **DO** search codebase for all filename references (`grep -r "old_name.py"`)

## Key Design Decisions

1. **Single-file architecture**: Entire game in `lucas_game.py` for simplicity—easy to audit, copy, modify
2. **Graceful degradation**: Visual-only mode if sound unavailable (kiosk reliability)
3. **Complex exit shortcut**: Ctrl+Shift+Esc prevents children from accidentally quitting
4. **On-screen exit hint**: Semi-transparent corner hint for parents (`draw_exit_hint()`)
5. **Raspberry Pi target**: Optimized for console framebuffer, no X11 overhead
6. **Title-screen key event passthrough**: `show_title_screen()` returns the `KEYDOWN` event that dismissed it. `main()` uses that event directly as the first game action—no keypress is wasted. If you refactor either function, preserve this coupling or the first key after the title screen will be silently ignored.

## Version Management

**ALWAYS update version strings before committing code changes** using semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** (X.0.0): Breaking changes (incompatible config format, removed features)
- **MINOR** (1.X.0): New features (new key display modes, config options)
- **PATCH** (1.0.X): Bug fixes, documentation updates, refactoring

**Version strings must be updated in ALL locations**:
```python
# 1. setup.py (3 locations)
'CFBundleVersion': '1.0.1',
'CFBundleShortVersionString': '1.0.1',
version='1.0.1',

# 2. pyproject.toml
version = "1.0.1"
```

**Why**: Versions must stay synchronized across build configurations. macOS app bundle displays CFBundleShortVersionString; pip/setuptools use version field. Mismatched versions cause confusion in bug reports and deployments.

**Workflow**:
1. Make code changes
2. Determine semver increment (major/minor/patch)
3. Update ALL four version locations (setup.py × 3, pyproject.toml × 1)
4. Commit with version in message: "chore: bump version to 1.0.1"
