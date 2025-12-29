#!/Users/warnes/src/lucas_game/venv/bin/python
"""
Random Color Screen with Sound
Fills the screen with a random color and plays a random tone when any key is pressed.
Press ESC to exit.
"""

import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Try to initialize sound, but continue if not available
SOUND_AVAILABLE = False
try:
    import numpy as np
    import sounddevice as sd
    SOUND_AVAILABLE = True
except (ImportError, NotImplementedError) as e:
    print(f"Sound not available: {e}")
    print("Continuing without sound support.")

# Set up fullscreen display
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Random Color Screen")

# Get screen dimensions
width, height = screen.get_size()

def generate_random_color():
    """Generate a random RGB color."""
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

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
    frequencies = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]  # C, D, E, F, G, A, B, C
    frequency = random.choice(frequencies)
    
    tone = generate_tone(frequency, duration=1.0)
    if tone is not None:
        import sounddevice as sd
        # Convert to float32 for sounddevice (range -1.0 to 1.0)
        tone_float = tone.astype(np.float32) / 32767.0
        sd.play(tone_float, 22050)
        sd.wait()  # Wait for the tone to finish playing

def main():
    """Main game loop."""
    clock = pygame.time.Clock()
    running = True
    
    # Set initial random color
    current_color = generate_random_color()
    screen.fill(current_color)
    pygame.display.flip()
    
    print("Random Color Screen")
    print("Press any key to change color and play a tone")
    print("Press ESC to exit")
    if not SOUND_AVAILABLE:
        print("\nNote: Sound is not available on this system")
        print("Visual feedback (♪) will be shown instead")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    # Change color and play tone
                    current_color = generate_random_color()
                    screen.fill(current_color)
                    pygame.display.flip()
                    play_random_tone()
                    # Clear any keystrokes that happened during tone playback
                    pygame.event.clear(pygame.KEYDOWN)
        
        clock.tick(60)  # 60 FPS
    
    pygame.quit()

if __name__ == "__main__":
    main()
