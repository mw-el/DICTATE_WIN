#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick ICO size checker - shows what sizes are in the .ico file"""
import struct
import os
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ico_path = "dictate.ico"

try:
    with open(ico_path, 'rb') as f:
        # Read ICO header
        reserved = struct.unpack('<H', f.read(2))[0]
        image_type = struct.unpack('<H', f.read(2))[0]
        num_images = struct.unpack('<H', f.read(2))[0]

        if reserved != 0 or image_type != 1:
            print("❌ Not a valid ICO file")
        else:
            print(f"✅ Valid ICO file with {num_images} image(s)\n")
            print("Sizes found in ICO:")
            print("-" * 40)

            sizes = []
            for i in range(num_images):
                width = struct.unpack('B', f.read(1))[0]
                height = struct.unpack('B', f.read(1))[0]
                # 0 means 256
                w = 256 if width == 0 else width
                h = 256 if height == 0 else height
                sizes.append(f"{w}×{h}")

                # Skip rest of directory entry (14 bytes)
                f.read(14)

            for size in sorted(set(sizes), key=lambda x: int(x.split('×')[0])):
                print(f"  • {size} px")

            print("\n" + "=" * 40)
            print("NEEDED for High-DPI Titlebar:")
            print("  • 16×16 (100% DPI)")
            print("  • 20×20 (125% DPI)")
            print("  • 24×24 (150% DPI)")
            print("  • 32×32 (200% DPI)")
            print("  • 40×40 (250% DPI)")
            print("  • 48×48 (300% DPI)")
            print("\nALSO recommended:")
            print("  • 64×64, 128×128, 256×256 (Taskbar)")

except FileNotFoundError:
    print(f"❌ File not found: {ico_path}")
except Exception as e:
    print(f"❌ Error: {e}")
