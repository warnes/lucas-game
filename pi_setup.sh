#!/bin/bash
# Raspberry Pi Setup Script for Lucas' Game
# Copyright (c) 2025 Gregory R. Warnes
# This script sets up a Raspberry Pi to boot directly into Lucas' Game

set -e  # Exit on error

echo "=========================================="
echo "Lucas' Game - Raspberry Pi Setup"
echo "=========================================="
echo ""

# Update system
echo "Step 1: Updating system..."
sudo apt update
sudo apt upgrade -y

# Install required system packages
echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    libsdl2-2.0-0 \
    libsdl2-mixer-2.0-0 \
    libsdl2-ttf-2.0-0 \
    libsdl2-image-2.0-0 \
    libportaudio2 \
    git

# Create game directory if it doesn't exist
echo ""
echo "Step 3: Setting up game directory..."
mkdir -p ~/lucas_game
cd ~/lucas_game

# Create Python virtual environment
echo ""
echo "Step 4: Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo ""
echo "Step 5: Installing Python packages..."
pip install numpy sounddevice

# Build pygame from source for better compatibility
echo ""
echo "Step 6: Building pygame (this may take a while)..."
pip install pygame --no-binary :all:

echo ""
echo "Step 7: Configuring auto-start..."

# Update .bashrc to auto-start the game
if ! grep -q "Auto-start Lucas' Game" ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# Auto-start Lucas' Game on console login (tty1 only)
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    echo "Starting Lucas' Game..."
    cd ~/lucas_game
    source venv/bin/activate
    
    # Loop to restart game if it crashes (but not if ESC was pressed)
    while true; do
        python random_color_screen.py
        EXIT_CODE=$?
        
        # Exit code 0 means normal exit (ESC pressed), don't restart
        if [ $EXIT_CODE -eq 0 ]; then
            break
        fi
        
        echo "Game crashed with exit code $EXIT_CODE, restarting in 3 seconds..."
        sleep 3
    done
fi
EOF
    echo "Auto-start configuration added to ~/.bashrc"
else
    echo "Auto-start already configured in ~/.bashrc"
fi

# Configure audio output to HDMI by default
echo ""
echo "Step 8: Configuring audio..."
sudo raspi-config nonint do_audio 2  # 0=auto, 1=headphones, 2=HDMI

# Optimize boot settings
echo ""
echo "Step 9: Optimizing boot settings..."
sudo raspi-config nonint do_boot_behaviour B2  # Console with autologin

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Make sure random_color_screen.py is in ~/lucas_game/"
echo "2. Reboot the Pi: sudo reboot"
echo "3. The game should start automatically after boot"
echo ""
echo "To manually test before rebooting:"
echo "  cd ~/lucas_game"
echo "  source venv/bin/activate"
echo "  python random_color_screen.py"
echo ""
echo "Press ESC to exit the game"
echo ""
