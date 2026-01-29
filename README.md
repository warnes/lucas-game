# Lucas Game

A simple interactive game that fills the screen with random colors and plays musical tones when keys are pressed.

## Features

- Full-screen display with random colors
- Musical tone generation (plays random notes from C major scale)
- Keyboard interaction
- Cross-platform sound support using sounddevice

## Requirements

- Python 3.7+
- pygame
- numpy
- sounddevice

## Installation

### macOS

1. Clone the repository:
```bash
git clone https://github.com/warnes/lucas-game.git
cd lucas-game
```

2. Install SDL2 libraries via Homebrew (required for pygame font and mixer modules):
```bash
brew install sdl2 sdl2_mixer sdl2_ttf sdl2_image
```

3. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install numpy sounddevice
```

4. Build pygame from source (to link with SDL2 libraries):
```bash
pip cache remove pygame  # Clear any cached wheels
pip install pygame --no-binary :all:
```

### Linux/Windows

1. Clone the repository:
```bash
git clone https://github.com/warnes/lucas-game.git
cd lucas-game
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install pygame numpy sounddevice
```

## Usage

Run the game:
```bash
./random_color_screen.py
```

Or:
```bash
python random_color_screen.py
```

### Controls

- **Any key**: Change color and play a random tone
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

The configuration file is automatically created with default values on first run. The default exit shortcut (Ctrl+Shift+Esc) is designed to be difficult for children to accidentally press.

### Preventing Accidental Trackpad Swipes (macOS)

On macOS, children may accidentally swipe on the trackpad, which can trigger Mission Control or switch between virtual desktops. To prevent this issue:

#### Option 1: Disable System Gestures (Recommended for Parents)

**Using System Preferences:**
1. Open **System Preferences** → **Trackpad**
2. Click on the **More Gestures** tab
3. Uncheck "**Swipe between full-screen apps**" (3-finger horizontal swipe)
4. Optionally uncheck "**Mission Control**" (3-finger swipe up)

**Using Terminal (Advanced):**
```bash
# Disable swipe between full-screen apps
defaults write com.apple.AppleMultitouchTrackpad TrackpadThreeFingerHorizSwipeGesture -int 0

# Disable Mission Control gesture
defaults write com.apple.dock showMissionControlGestureEnabled -bool false

# Restart Dock to apply changes
killall Dock
```

To re-enable these features later, either use System Preferences or run:
```bash
defaults delete com.apple.AppleMultitouchTrackpad TrackpadThreeFingerHorizSwipeGesture
defaults delete com.apple.dock showMissionControlGestureEnabled
killall Dock
```

#### Option 2: Use External Keyboard

For the best experience, use an external keyboard with the trackpad disabled or covered.

**Note**: The game automatically hides the mouse cursor and captures mouse events, but macOS system gestures operate at the OS level and cannot be prevented by the application itself. See `TRACKPAD_SWIPE_RESEARCH.md` for detailed technical information.

## How It Works

The game uses pygame for graphics and event handling, and sounddevice for audio generation. Each keypress triggers a random color fill and plays a musical note from the C major scale with a 1-second duration.

## Building macOS Application

To create a standalone macOS application:

1. Follow the macOS installation instructions above

2. Run the build script:
```bash
./build_macos.sh
```

3. The application will be created in `dist/Lucas' Game.app`

4. Install by dragging to Applications folder or run:
```bash
open "dist/Lucas' Game.app"
```

The build script automatically:
- Generates an application icon
- Creates a standalone .app bundle with all dependencies
- Signs the application for macOS

## License

MIT License - Copyright (c) 2025 Gregory R. Warnes
