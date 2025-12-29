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
- **ESC**: Exit the game

## How It Works

The game uses pygame for graphics and event handling, and sounddevice for audio generation. Each keypress triggers a random color fill and plays a musical note from the C major scale with a 1-second duration.

## License

MIT
