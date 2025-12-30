#!/usr/bin/env python3
"""
Generate icon for Lucas' Game
Creates a simple colorful icon with a key symbol
"""

import pygame
import sys

# Initialize Pygame
pygame.init()

# Icon sizes for macOS .icns (we'll create the largest and let iconutil scale)
ICON_SIZE = 1024

# Create surface
surface = pygame.Surface((ICON_SIZE, ICON_SIZE), pygame.SRCALPHA)

# Create gradient background
for y in range(ICON_SIZE):
    color_r = int(255 * (1 - y / ICON_SIZE))
    color_g = int(200 * (y / ICON_SIZE))
    color_b = int(255 * (0.5 + 0.5 * y / ICON_SIZE))
    pygame.draw.line(surface, (color_r, color_g, color_b, 255), (0, y), (ICON_SIZE, y))

# Draw a key shape
key_width = int(ICON_SIZE * 0.7)
key_height = int(ICON_SIZE * 0.5)
key_x = (ICON_SIZE - key_width) // 2
key_y = (ICON_SIZE - key_height) // 2

key_rect = pygame.Rect(key_x, key_y, key_width, key_height)
border_radius = key_height // 6

# Draw shadow
shadow_offset = 15
shadow_color = (50, 50, 50, 180)
shadow_rect = pygame.Rect(key_x + shadow_offset, key_y + shadow_offset, key_width, key_height)
pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=border_radius)

# Draw key body (white)
pygame.draw.rect(surface, (255, 255, 255, 255), key_rect, border_radius=border_radius)

# Draw key border
pygame.draw.rect(surface, (100, 100, 100, 255), key_rect, width=8, border_radius=border_radius)

# Draw text "L" on the key
font_size = int(key_height * 0.6)
font = pygame.font.Font(None, font_size)
text = font.render("L", True, (50, 50, 50))
text_x = key_x + (key_width - text.get_width()) // 2
text_y = key_y + (key_height - text.get_height()) // 2
surface.blit(text, (text_x, text_y))

# Save as PNG
pygame.image.save(surface, "icon.png")
print("Icon saved as icon.png")

# Instructions for creating .icns
print("\nTo create the .icns file for macOS:")
print("1. Create an iconset directory:")
print("   mkdir icon.iconset")
print("2. Create different sizes:")
print("   sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png")
print("   sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png")
print("   sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png")
print("   sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png")
print("   sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png")
print("   sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png")
print("   sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png")
print("   sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png")
print("   sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png")
print("   sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png")
print("3. Convert to .icns:")
print("   iconutil -c icns icon.iconset")
