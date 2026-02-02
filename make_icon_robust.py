#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust Multi-Size ICO Generator
================================
Manually writes ICO file format to ensure all sizes are included.
Works around Pillow's buggy multi-size ICO save.
"""

import sys
import os
import struct
from io import BytesIO

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Install with: pip install pillow")
    sys.exit(1)

SIZES = [16, 20, 24, 28, 32, 40, 48, 64, 96, 128, 256]


def create_ico_manually(images, output_path):
    """
    Manually write ICO file format with multiple sizes

    ICO Format:
    - Header (6 bytes): Reserved(2), Type(2), Count(2)
    - Directory entries (16 bytes each): Width, Height, Colors, Reserved, Planes, BPP, Size, Offset
    - Image data (PNG format for each size)
    """

    # Prepare PNG data for each image
    png_data_list = []
    for img in images:
        png_buffer = BytesIO()
        img.save(png_buffer, format='PNG')
        png_data = png_buffer.getvalue()
        png_data_list.append(png_data)

    with open(output_path, 'wb') as f:
        # Write ICO header
        f.write(struct.pack('<H', 0))       # Reserved (must be 0)
        f.write(struct.pack('<H', 1))       # Type (1 = ICO)
        f.write(struct.pack('<H', len(images)))  # Number of images

        # Calculate offsets
        header_size = 6  # ICO header
        dir_entry_size = 16  # per image
        offset = header_size + (dir_entry_size * len(images))

        # Write directory entries
        for img, png_data in zip(images, png_data_list):
            width, height = img.size

            # Directory entry (16 bytes)
            f.write(struct.pack('B', width if width < 256 else 0))   # Width (0 = 256)
            f.write(struct.pack('B', height if height < 256 else 0)) # Height (0 = 256)
            f.write(struct.pack('B', 0))     # Color palette size (0 = no palette)
            f.write(struct.pack('B', 0))     # Reserved
            f.write(struct.pack('<H', 1))    # Color planes
            f.write(struct.pack('<H', 32))   # Bits per pixel (32-bit RGBA)
            f.write(struct.pack('<I', len(png_data)))  # Size of image data
            f.write(struct.pack('<I', offset))         # Offset to image data

            offset += len(png_data)

        # Write image data (PNG format)
        for png_data in png_data_list:
            f.write(png_data)


def main():
    if len(sys.argv) < 2:
        print("Usage: python make_icon_robust.py <source_image>")
        sys.exit(1)

    source_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "dictate.ico"

    print(f"Loading: {source_path}")

    try:
        source = Image.open(source_path)
    except Exception as e:
        print(f"ERROR: Cannot load image: {e}")
        sys.exit(1)

    if source.mode != 'RGBA':
        source = source.convert('RGBA')

    print(f"Source: {source.width}x{source.height} px")
    print(f"\nGenerating {len(SIZES)} sizes...")

    icons = []
    for size in SIZES:
        icon = source.resize((size, size), Image.Resampling.LANCZOS)
        icons.append(icon)
        print(f"  {size}x{size}")

    print(f"\nWriting ICO file: {output_path}")
    create_ico_manually(icons, output_path)

    # Verify
    if os.path.exists(output_path):
        size_kb = os.path.getsize(output_path) / 1024

        # Read back and verify
        with open(output_path, 'rb') as f:
            f.read(2)  # reserved
            f.read(2)  # type
            num_images = struct.unpack('<H', f.read(2))[0]

        print(f"\nSuccess! {output_path}")
        print(f"  File size: {size_kb:.1f} KB")
        print(f"  Images: {num_images} sizes")

        if num_images == len(SIZES):
            print(f"  Status: OK - All {len(SIZES)} sizes included!")
        else:
            print(f"  Status: Warning - Expected {len(SIZES)}, got {num_images}")


if __name__ == '__main__':
    main()
