#!/Users/warnes/src/lucas_game/venv/bin/python
"""
Random Color Screen with Sound
Fills the screen with a random color and plays a random tone when any key is pressed.

Copyright (c) 2025 Gregory R. Warnes
License: MIT
"""

import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Initialize font module
try:
    pygame.font.init()
except Exception as e:
    print(f"Warning: Font initialization issue: {e}")

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

def show_title_screen(screen):
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
    instructions = [
        "Press any key to see it displayed",
        "with a random color and sound!",
        "",
        "Press ESC to exit",
        "",
        "Press any key to start..."
    ]
    
    y_offset = screen_height // 2.5
    for instruction in instructions:
        text = instruction_font.render(instruction, True, (200, 200, 200))
        x = (screen_width - text.get_width()) // 2
        screen.blit(text, (x, y_offset))
        y_offset += 60
    
    # Copyright
    copyright_font = pygame.font.Font(None, 32)
    copyright_text = copyright_font.render("© 2025 Gregory R. Warnes", True, (150, 150, 150))
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
                if event.key == pygame.K_ESCAPE:
                    return None
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
    shadow_rect = pygame.Rect(key_x + shadow_offset, key_y + shadow_offset, key_width, key_height)
    pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=border_radius)
    
    # Draw key body
    pygame.draw.rect(screen, color, key_rect, border_radius=border_radius)
    
    # Draw key border
    border_color = tuple(min(255, c + 50) for c in color)
    pygame.draw.rect(screen, border_color, key_rect, width=5, border_radius=border_radius)
    
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
    
    # Hide mouse cursor to reduce distractions and discourage trackpad use
    pygame.mouse.set_visible(False)
    
    # Show title screen and get the starting key event
    start_event = show_title_screen(screen)
    if start_event is None:
        pygame.quit()
        return
    
    running = True
    
    # Use the title screen key press for the first action
    current_color = generate_random_color()
    screen.fill(current_color)
    key_name = get_key_name(start_event.key)
    draw_key(screen, key_name, current_color)
    pygame.display.flip()
    
    print("Random Color Screen")
    print("Press any key to change color and play a tone")
    print("Press ESC to exit")
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
                if event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    # Change color and play tone
                    current_color = generate_random_color()
                    screen.fill(current_color)
                    
                    # Get the key name and draw it
                    key_name = get_key_name(event.key)
                    draw_key(screen, key_name, current_color)
                    
                    pygame.display.flip()
                    play_random_tone()
                    # Clear any keystrokes that happened during tone playback
                    pygame.event.clear(pygame.KEYDOWN)
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
                # Capture mouse/trackpad events to prevent them from propagating
                # Note: This does not prevent macOS system gestures (Mission Control, etc.)
                # which operate at the OS level. See TRACKPAD_SWIPE_RESEARCH.md for details.
                pass
        
        clock.tick(60)  # 60 FPS
    
    pygame.quit()

if __name__ == "__main__":
    main()
