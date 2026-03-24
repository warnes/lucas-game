# Lucas' Game

A fullscreen keyboard game for young children. It starts on a title screen, then shows each pressed key inside a large on-screen key shape with a new random color and, when audio support is available, plays a musical tone.

## Features

- Fullscreen title screen with start and exit instructions
- Large on-screen key display that shows the most recently pressed key
- Random full-screen color theme on every key press
- Musical tone playback using random notes from the C major scale
- Configurable exit shortcut with an on-screen corner hint
- Visual-only fallback when audio libraries or audio devices are unavailable

## Requirements

- Python 3.7+
- pygame
- platformdirs

Optional for audio support:

- numpy
- sounddevice

## Installation

### macOS

1. Clone the repository:

```bash
git clone https://github.com/warnes/lucas-game.git
cd lucas-game
```

1. Install SDL2 libraries via Homebrew (required for pygame font and mixer modules):

```bash
brew install sdl2 sdl2_mixer sdl2_ttf sdl2_image
```

1. Create a virtual environment and install the dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install platformdirs numpy sounddevice
```

1. Build pygame from source (to link with the installed SDL2 libraries):

```bash
pip cache remove pygame  # Clear any cached wheels
pip install pygame --no-binary :all:
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

## Usage

Run the game:

```bash
python lucas_game.py
```

### Controls

- **Any key on the title screen**: Start the game
- **Any key during the game**: Display that key, change the colors, and play a tone if audio is available
- **Ctrl+Shift+Esc**: Exit the game (default, configurable)

**Note**: A small hint showing the exit shortcut is displayed in the bottom-right corner of the screen while the game is running, so parents can easily see how to exit.

### Configuration

The exit shortcut can be customized by editing the configuration file located at:

- **Linux/Unix**: `~/.config/lucas-game/config.json` (or `$XDG_CONFIG_HOME/lucas-game/config.json`)
- **macOS**: `~/Library/Application Support/lucas-game/config.json`
- **Windows**: `%APPDATA%\lucas-game\config.json` (typically `C:\Users\<username>\AppData\Roaming\lucas-game\config.json`)

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

- **Correct**: `"ESCAPE"`, `"Q"`, `"F10"`, `"RETURN"`
- **Incorrect**: `"K_ESCAPE"`, `"K_Q"`, `"esc"` (case-sensitive)

The modifier keys (`ctrl`, `shift`, `alt`) can be set to `true` or `false`.

The configuration file is automatically created with default values on first run. If the file is missing, malformed, or has the wrong types, the game falls back to the default shortcut and rewrites the config. The default exit shortcut (Ctrl+Shift+Esc) is designed to be difficult for children to accidentally press.

## How It Works

The game uses `pygame` for fullscreen graphics and keyboard input, `platformdirs` to store its config file in the correct OS-specific location, and optionally `numpy` plus `sounddevice` for audio generation. The title screen waits for the first key press, then each non-exit key press:

- picks a new random color
- draws a large rounded key that fills about 75% of the screen
- shows the pressed key name in the center
- redraws the exit hint in the lower-right corner
- plays a 1-second tone chosen from the C major scale when audio is available

When audio is not available, the game continues to run and prints `♪` in the terminal as minimal feedback instead of playing sound.

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
- Recreates the `build/` and `dist/` directories
- Creates a standalone `.app` bundle

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

## License

MIT License - Copyright (c) 2025 Gregory R. Warnes
