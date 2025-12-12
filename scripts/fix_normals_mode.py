#!/usr/bin/env python3
"""
Simple fix for VXL normals mode byte.
Sets the normals mode to 4 (RA2 standard) for all limbs.
"""

import struct
import sys
import os

def fix_normals_mode(file_path):
    """Fix the normals mode byte in a VXL file."""
    print(f"Reading: {file_path}")

    with open(file_path, 'rb') as f:
        data = bytearray(f.read())

    # Verify it's a VXL
    if data[0:16] != b'Voxel Animation\x00':
        print("Error: Not a valid VXL file")
        return False

    num_limbs = struct.unpack_from('<I', data, 20)[0]
    body_size = struct.unpack_from('<I', data, 28)[0]

    # Calculate tailer offset
    limb_header_start = 34 + 768  # 802
    body_start = limb_header_start + (num_limbs * 28)
    tailer_start = body_start + body_size

    print(f"Limbs: {num_limbs}")
    print(f"Body size: {body_size}")
    print(f"Tailer start: {tailer_start}")

    # Fix normals mode for each limb
    for i in range(num_limbs):
        tailer_offset = tailer_start + (i * 92)
        normals_mode_offset = tailer_offset + 83

        old_mode = data[normals_mode_offset]
        data[normals_mode_offset] = 4  # RA2 standard

        # Get dimensions for info
        dim_x = data[tailer_offset + 80]
        dim_y = data[tailer_offset + 81]
        dim_z = data[tailer_offset + 82]

        print(f"  Limb {i}: {dim_x}x{dim_y}x{dim_z}, normals mode {old_mode} -> 4")

    # Write back
    with open(file_path, 'wb') as f:
        f.write(data)

    print("Fixed!")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_normals_mode.py <file.vxl>")
        sys.exit(1)

    fix_normals_mode(sys.argv[1])
