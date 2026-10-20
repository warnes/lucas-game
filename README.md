# Lucas' Game

A fullscreen keyboard game for young children. It starts on a title screen, then shows each pressed key inside a large on-screen key shape with a new random color and, when audio support is available, plays a musical tone.

## Features

- Fullscreen title screen with start and exit instructions
- Large on-screen key display that shows the most recently pressed key
- Random full-screen color theme on every key press
- Musical tone playback using random notes from the C major scale
- Configurable exit shortcut with an on-screen corner hint
- Visual-only fallback when audio libraries or audio devices are unavailable
- On macOS, media and brightness keys (including the Touch Bar) are suppressed
  while the game runs, and restored on exit

## Requirements

- Python 3.10+
- pygame
- platformdirs

Optional for audio support:

- numpy
- sounddevice

**Note on the Python version**: `lucas_game.py` itself uses no syntax newer than
Python 3.7, but current releases of its dependencies do have floors — as of
this writing `platformdirs` 4.5.1 requires 3.10+ and `numpy` 2.4.1 requires
3.11+. On an older interpreter pip will fall back to older dependency releases,
which is untested. Python 3.11+ is recommended if you want audio.

## Installation

### macOS

1. Clone the repository:

```bash
git clone https://github.com/warnes/lucas-game.git
cd lucas-game
```

1. Create a virtual environment and install the dependencies:

```bash
python3.13 -m venv venv       # see the interpreter note below
source venv/bin/activate
pip install pygame platformdirs numpy sounddevice
```

**Use pygame's binary wheel — do not build it from source, and do not
`brew install sdl2`.** Earlier versions of this README told you to do both,
because macOS pygame wheels once shipped without working font and mixer
support. That is no longer true (verified on pygame 2.6.1: `pygame.font` and
`pygame.mixer` both initialize from the wheel), and following the old advice now
produces an app that **hangs on launch from the Dock**:

- `brew install sdl2` today installs **sdl2-compat**, a SDL2-API shim over SDL3.
- Building pygame from source links it against that shim, and `build_macos.sh`
  bundles the shim into the `.app`.
- sdl2-compat's dylib initializer calls `-[NSApplication finishLaunching]`. Under
  LaunchServices that runs inside `dlopen()` while dyld holds the loader lock,
  AppKit tries to build the menu bar, and the process **deadlocks during
  `import pygame`** — before any window is created. The icon bounces forever and
  nothing appears. Running the very same binary from a terminal works fine,
  which makes this easy to misdiagnose.

`build_macos.sh` now fails the build if sdl2-compat ends up in the bundle.

**Interpreter note**: pygame does not yet publish macOS wheels for CPython
3.14, so build the app with **Python 3.11–3.13**. The game itself runs fine on
3.14; it is only the `.app` bundle that needs a wheel-provided SDL2.

1. Install the game itself:

```bash
pip install .          # or: pip install -e .   for a development install
```

If `numpy` or `sounddevice` are unavailable, the game still runs in visual-only mode without audio.

### Linux/Windows

1. Clone the repository:

```bash
git clone https://github.com/warnes/lucas-game.git
cd lucas-game
```

1. Create a virtual environment and install the dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pygame platformdirs numpy sounddevice
```

For a visual-only install, `pygame` and `platformdirs` are sufficient.

1. Install the game itself:

```bash
pip install .          # or: pip install -e .   for a development install
```

## Usage

If you installed the package (`pip install .`), run it by name:

```bash
lucas-game
```

Otherwise run the script directly from the repository:

```bash
python lucas_game.py
```

**Note**: run `python lucas_game.py`, not `./lucas_game.py` — the shebang line
points at a specific developer's virtual environment.

### Controls

- **Any key on the title screen**: Start the game
- **Any key during the game**: Display that key, change the colors, and play a tone if audio is available
- **Ctrl+Shift+Esc**: Exit the game (default, configurable)

**Note**: A small hint showing the exit shortcut is displayed in the bottom-right corner of the screen while the game is running, so parents can easily see how to exit.

### Configuration

The exit shortcut can be customized by editing the configuration file located at:

- **Linux/Unix**: `~/.config/lucas-game/config.json` (or `$XDG_CONFIG_HOME/lucas-game/config.json`)
- **macOS**: `~/Library/Application Support/lucas-game/config.json`
- **Windows**: `%LOCALAPPDATA%\warnes\lucas-game\config.json` (typically `C:\Users\<username>\AppData\Local\warnes\lucas-game\config.json`)

Example configuration:

```json
{
    "exit_shortcut": {
        "key": "ESCAPE",
        "ctrl": true,
        "shift": true,
        "alt": false
    }
}
```

The `key` field should be a pygame key constant name **without** the `K_` prefix:

- **Correct**: `"ESCAPE"`, `"Q"`, `"F10"`, `"RETURN"`, `"SPACE"`, `"1"`
- **Incorrect**: `"K_ESCAPE"`, `"K_Q"` — the `K_` prefix must not be included

Letter case is not significant: `"Q"` and `"q"` both work, as do `"ESCAPE"` and
`"escape"`. (pygame itself spells letter constants in lowercase — `K_q` — and
everything else in uppercase — `K_ESCAPE`, `K_F10`. The game accepts either.)

If the key name cannot be resolved at all, the game prints a warning, falls back
to `ESCAPE`, and the on-screen hint shows the shortcut that will actually exit
rather than the one that was requested.

The modifier keys (`ctrl`, `shift`, `alt`) can be set to `true` or `false`. A
modifier set to `false` must be *absent* when the shortcut is pressed, so
`Ctrl+Shift+Alt+Esc` will not trigger the default `Ctrl+Shift+Esc` shortcut.

The configuration file is automatically created with default values on first run. If the file is missing, malformed, or has the wrong types, the game falls back to the default shortcut and rewrites the config. The default exit shortcut (Ctrl+Shift+Esc) is designed to be difficult for children to accidentally press.

## How It Works

The game uses `pygame` for fullscreen graphics and keyboard input, `platformdirs` to store its config file in the correct OS-specific location, and optionally `numpy` plus `sounddevice` for audio generation. The title screen waits for the first key press, then each non-exit key press:

- picks a new random color
- draws a large rounded key that fills about 75% of the screen
- shows the pressed key name in the center
- redraws the exit hint in the lower-right corner
- plays a 1-second tone chosen from the C major scale when audio is available

When audio is not available, the game continues to run and prints `♪` in the terminal as minimal feedback instead of playing sound.

### Media key suppression (macOS)

While the game is running on macOS it remaps the system media and brightness
keys to F13 using `hidutil`, so a child cannot change the volume, screen
brightness, or media playback. The Touch Bar emits the same HID events, so it is
covered too. The suppression is undone when the game exits — including on
`SIGTERM` and on an unhandled crash.

**If you already use `hidutil` yourself, the game leaves your mappings alone.**
`hidutil` has a single system-wide mapping list and setting it replaces the
whole list, so there is no way to add the game's entries without discarding
yours and no way to put yours back afterwards. Rather than destroy them, the
game detects existing mappings at startup, prints a note, and skips media-key
suppression entirely for that session. A common case is a Caps Lock remap.

This changes system state only for the lifetime of the process, and only when
the game actually started — importing the module (for example, running the test
suite) does not touch your key mappings. If the game is killed with `SIGKILL`
(`kill -9`) the cleanup cannot run; `hidutil property --set
'{"UserKeyMapping":[]}'` clears the remapping. Note that this command clears
**all** user key mappings, not just the game's — which is safe only because the
game refuses to run its suppression when you have any of your own.

## Testing

The test suite runs headlessly — it uses SDL's dummy video driver, so it will
not take over your screen:

```bash
pip install -e ".[dev]"
pytest
```

## Building macOS Application

To create a standalone macOS application:

1. Follow the macOS installation instructions above

1. Run the build script:

```bash
./build_macos.sh
```

1. The application will be created in `dist/Lucas' Game.app`

1. Install by dragging to Applications folder or run:

```bash
open "dist/Lucas' Game.app"
```

The build script automatically:

- Activates the virtual environment
- Installs `py2app` if needed
- Generates an application icon if one does not already exist
- Removes `build/` and the previous `.app`, keeping the `dist/Applications`
  symlink that makes the drag-and-drop install work
- Creates a standalone `.app` bundle

The bundle embeds its own Python interpreter and vendors `pygame`, `numpy`,
`sounddevice` and `platformdirs`, so it runs on a Mac with no Python
environment installed.

Two things to know about the resulting `.app`:

- **It is unsigned** (`codesign -dv` reports "code object is not signed at
  all"), so Gatekeeper will refuse it on first launch — use right-click → Open,
  or run `xattr -dr com.apple.quarantine "dist/Lucas' Game.app"`.
- **It is built for the architecture of the build machine only**, not as a
  universal binary. A bundle built on an Intel Mac needs Rosetta 2 to run on
  Apple Silicon. Check with
  `file "dist/Lucas' Game.app/Contents/MacOS/python"`.

## Raspberry Pi Kiosk

The Pi is a first-class deployment target: the game runs fullscreen on the
console framebuffer, with auto-login and auto-restart, on Raspberry Pi OS Lite —
no desktop environment. Setup, imaging, and troubleshooting are in
[RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md).

## Web Version

A browser-based version of Lucas' Game lives in the `web/` directory. It uses
HTML, CSS, and the Web Audio API — no plugins or server required. The build
output is a single self-contained `dist/index.html` that runs from `file://`
(e.g., on a Raspberry Pi Chromium kiosk).

### Requirements

- [Node.js](https://nodejs.org/) 18+

### Build

```bash
cd web
npm install
npm run build
# → dist/index.html (single self-contained file)
```

### Development server

```bash
cd web
npm run dev
# Open http://localhost:5173
```

### Web version features

- Fullscreen title screen — press any key or click to start
- First key press requests browser fullscreen
- Large on-screen key display with random color theme on every key press
- Musical tones from the C major scale via the Web Audio API
- No installation, no dependencies at runtime — open `dist/index.html` directly

## Contributing

Pull requests target the `devel` branch, not `main`. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the branch layout, the test-suite
constraints, and the parts of the code that need extra care.

## License

MIT License - Copyright (c) 2025 Gregory R. Warnes
