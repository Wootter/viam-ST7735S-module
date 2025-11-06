#!/usr/bin/env python3
"""
Test script for ST7735S display
Run this on your Raspberry Pi to test if the display works
"""

import time
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7735

print("ST7735S Display Test")
print("=" * 50)

# Configuration (adjust if you used different pins)
CS_PIN = 8
DC_PIN = 25
RESET_PIN = 24

try:
    print(f"\n1. Setting up GPIO pins...")
    print(f"   CS Pin: GPIO {CS_PIN}")
    print(f"   DC Pin: GPIO {DC_PIN}")
    print(f"   Reset Pin: GPIO {RESET_PIN}")
    
    cs_pin = digitalio.DigitalInOut(getattr(board, f"D{CS_PIN}"))
    dc_pin = digitalio.DigitalInOut(getattr(board, f"D{DC_PIN}"))
    reset_pin = digitalio.DigitalInOut(getattr(board, f"D{RESET_PIN}"))
    print("   ✓ GPIO pins configured")
    
    print("\n2. Initializing SPI...")
    spi = board.SPI()
    print("   ✓ SPI initialized")
    
    print("\n3. Initializing ST7735S display...")
    display = st7735.ST7735S(
        spi,
        cs=cs_pin,
        dc=dc_pin,
        rst=reset_pin,
        rotation=90,
        width=128,
        height=160,
        bgr=True
    )
    print("   ✓ Display initialized!")
    print(f"   Display size: {display.width}x{display.height}")
    
    # Test 1: Fill screen with colors
    print("\n4. Testing colors...")
    colors = [
        ("Red", (255, 0, 0)),
        ("Green", (0, 255, 0)),
        ("Blue", (0, 0, 255)),
        ("White", (255, 255, 255)),
        ("Black", (0, 0, 0))
    ]
    
    for name, color in colors:
        print(f"   Showing {name}...")
        image = Image.new("RGB", (display.width, display.height), color)
        display.image(image)
        time.sleep(1)
    
    # Test 2: Draw shapes
    print("\n5. Testing shapes...")
    image = Image.new("RGB", (display.width, display.height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Circle
    draw.ellipse((10, 10, 50, 50), fill=(255, 0, 0))
    # Rectangle
    draw.rectangle((70, 10, 110, 50), fill=(0, 255, 0))
    # Line
    draw.line((10, 70, 110, 70), fill=(0, 0, 255), width=3)
    # Text
    draw.text((20, 90), "WORKS!", fill=(255, 255, 255))
    
    display.image(image)
    print("   ✓ Shapes displayed")
    
    time.sleep(2)
    
    # Test 3: Happy face
    print("\n6. Testing happy face...")
    image = Image.new("RGB", (display.width, display.height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    center_x = display.width // 2
    eye_y = display.height // 3
    mouth_y = int(display.height * 0.65)
    
    # Eyes
    draw.ellipse((center_x - 50, eye_y - 10, center_x - 30, eye_y + 10), fill=(0, 255, 255))
    draw.ellipse((center_x + 30, eye_y - 10, center_x + 50, eye_y + 10), fill=(0, 255, 255))
    
    # Smile
    draw.arc((center_x - 30, mouth_y - 15, center_x + 30, mouth_y + 20), 
             start=0, end=180, fill=(255, 255, 0), width=4)
    
    display.image(image)
    print("   ✓ Happy face displayed")
    
    print("\n" + "=" * 50)
    print("✓ ALL TESTS PASSED!")
    print("Your ST7735S display is working correctly!")
    print("=" * 50)
    
    # Keep display on for 5 seconds
    print("\nKeeping display on for 5 seconds...")
    time.sleep(5)
    
    # Clear display
    print("Clearing display...")
    image = Image.new("RGB", (display.width, display.height), (0, 0, 0))
    display.image(image)
    print("Done!")

except ImportError as e:
    print(f"\n✗ ERROR: Missing library")
    print(f"  {e}")
    print("\nInstall required libraries:")
    print("  pip3 install adafruit-circuitpython-rgb-display pillow")
    
except ValueError as e:
    print(f"\n✗ ERROR: Invalid pin configuration")
    print(f"  {e}")
    print("\nCheck your pin numbers in this script")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("\nPossible issues:")
    print("  1. SPI not enabled - run: sudo raspi-config → Interface Options → SPI → Enable")
    print("  2. Wrong pin connections - check wiring")
    print("  3. Display not powered (3.3V to VCC and BLK)")
    print("  4. Bad connections - try different jumper wires")
