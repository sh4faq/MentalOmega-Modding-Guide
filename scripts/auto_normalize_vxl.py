#!/usr/bin/env python3
"""
Auto-Normalize VXL files for Red Alert 2/Yuri's Revenge
Calculates proper lighting normals for each voxel based on neighboring voxels.
"""

import struct
import sys
import math
import os

# RA2 Normals Table (36 normals, mode 4)
# These are the pre-defined normal vectors used by the game
NORMALS_TABLE = [
    (0.0, 0.0, 1.0),      # 0: Up
    (0.0, 0.0, -1.0),     # 1: Down
    (1.0, 0.0, 0.0),      # 2: Right
    (-1.0, 0.0, 0.0),     # 3: Left
    (0.0, 1.0, 0.0),      # 4: Front
    (0.0, -1.0, 0.0),     # 5: Back
    (0.707, 0.0, 0.707),  # 6: Up-Right
    (-0.707, 0.0, 0.707), # 7: Up-Left
    (0.0, 0.707, 0.707),  # 8: Up-Front
    (0.0, -0.707, 0.707), # 9: Up-Back
    (0.707, 0.0, -0.707), # 10: Down-Right
    (-0.707, 0.0, -0.707),# 11: Down-Left
    (0.0, 0.707, -0.707), # 12: Down-Front
    (0.0, -0.707, -0.707),# 13: Down-Back
    (0.707, 0.707, 0.0),  # 14: Right-Front
    (-0.707, 0.707, 0.0), # 15: Left-Front
    (0.707, -0.707, 0.0), # 16: Right-Back
    (-0.707, -0.707, 0.0),# 17: Left-Back
    (0.577, 0.577, 0.577),  # 18: Up-Right-Front
    (-0.577, 0.577, 0.577), # 19: Up-Left-Front
    (0.577, -0.577, 0.577), # 20: Up-Right-Back
    (-0.577, -0.577, 0.577),# 21: Up-Left-Back
    (0.577, 0.577, -0.577), # 22: Down-Right-Front
    (-0.577, 0.577, -0.577),# 23: Down-Left-Front
    (0.577, -0.577, -0.577),# 24: Down-Right-Back
    (-0.577, -0.577, -0.577),# 25: Down-Left-Back
    # Additional edge normals
    (0.894, 0.447, 0.0),  # 26
    (-0.894, 0.447, 0.0), # 27
    (0.894, -0.447, 0.0), # 28
    (-0.894, -0.447, 0.0),# 29
    (0.447, 0.0, 0.894),  # 30
    (-0.447, 0.0, 0.894), # 31
    (0.447, 0.0, -0.894), # 32
    (-0.447, 0.0, -0.894),# 33
    (0.0, 0.447, 0.894),  # 34
    (0.0, -0.447, 0.894), # 35
]

def normalize_vector(v):
    """Normalize a 3D vector."""
    length = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    if length < 0.0001:
        return (0.0, 0.0, 1.0)  # Default to up
    return (v[0]/length, v[1]/length, v[2]/length)

def dot_product(v1, v2):
    """Calculate dot product of two 3D vectors."""
    return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]

def find_closest_normal(normal):
    """Find the index of the closest pre-defined normal."""
    normal = normalize_vector(normal)
    best_index = 0
    best_dot = -2.0

    for i, table_normal in enumerate(NORMALS_TABLE):
        d = dot_product(normal, table_normal)
        if d > best_dot:
            best_dot = d
            best_index = i

    return best_index

def read_vxl_structure(data):
    """Read VXL file structure and return parsed data."""
    # Header
    if data[0:16] != b'Voxel Animation\x00':
        raise ValueError("Not a valid VXL file")

    num_limbs = struct.unpack_from('<I', data, 20)[0]
    body_size = struct.unpack_from('<I', data, 28)[0]

    # Limb headers start at 34 (palette starts at 34, is 768 bytes, then limb headers)
    limb_header_start = 34 + 768  # 802

    limbs = []
    for i in range(num_limbs):
        offset = limb_header_start + (i * 28)
        name = data[offset:offset+16].split(b'\x00')[0].decode('ascii', errors='ignore')
        limbs.append({
            'name': name,
            'header_offset': offset
        })

    # Body data offset
    body_start = limb_header_start + (num_limbs * 28)

    # Tailer offset
    tailer_start = body_start + body_size

    return {
        'num_limbs': num_limbs,
        'body_size': body_size,
        'limb_header_start': limb_header_start,
        'body_start': body_start,
        'tailer_start': tailer_start,
        'limbs': limbs
    }

def read_vxl_voxels(data, structure):
    """Read all voxels from VXL file."""
    tailer_start = structure['tailer_start']

    # For each limb, read dimensions and voxel data
    all_voxels = []

    for limb_idx in range(structure['num_limbs']):
        tailer_offset = tailer_start + (limb_idx * 92)

        # Span data info from tailer
        span_start = struct.unpack_from('<I', data, tailer_offset)[0]
        span_end = struct.unpack_from('<I', data, tailer_offset + 4)[0]
        span_data = struct.unpack_from('<I', data, tailer_offset + 8)[0]

        # Dimensions at offset 80 in tailer
        dim_x = data[tailer_offset + 80]
        dim_y = data[tailer_offset + 81]
        dim_z = data[tailer_offset + 82]

        print(f"  Limb {limb_idx}: {dim_x}x{dim_y}x{dim_z}")

        # Create 3D grid
        voxels = {}  # (x, y, z) -> (color, normal)

        # Parse span data
        body_start = structure['body_start']

        # Read span start/end offsets
        span_starts = []
        span_ends = []
        for y in range(dim_y):
            for x in range(dim_x):
                idx = y * dim_x + x
                s_start = struct.unpack_from('<I', data, body_start + span_start + idx * 4)[0]
                s_end = struct.unpack_from('<I', data, body_start + span_end + idx * 4)[0]
                span_starts.append(s_start)
                span_ends.append(s_end)

        # Read voxel data from spans
        voxel_data_base = body_start + span_data

        for y in range(dim_y):
            for x in range(dim_x):
                idx = y * dim_x + x
                if span_starts[idx] == -1 or span_starts[idx] == 0xFFFFFFFF:
                    continue

                # Read spans for this column
                pos = voxel_data_base + span_starts[idx]
                z = 0

                while z < dim_z:
                    if pos >= len(data):
                        break

                    skip = data[pos]
                    count = data[pos + 1]
                    pos += 2

                    if skip == 0 and count == 0:
                        break

                    z += skip

                    # Read voxels
                    for i in range(count):
                        if z + i < dim_z and pos + i * 2 + 1 < len(data):
                            color = data[pos + i * 2]
                            normal = data[pos + i * 2 + 1]
                            voxels[(x, y, z + i)] = (color, normal)

                    pos += count * 2
                    z += count

                    # Skip count at end
                    if pos < len(data):
                        end_count = data[pos]
                        pos += 1
                        z += end_count

        all_voxels.append({
            'dims': (dim_x, dim_y, dim_z),
            'voxels': voxels,
            'tailer_offset': tailer_offset
        })

    return all_voxels

def calculate_surface_normal(voxels, x, y, z, dims):
    """Calculate surface normal for a voxel based on empty neighbors."""
    dx, dy, dz = dims
    normal = [0.0, 0.0, 0.0]

    # Check all 6 cardinal directions
    neighbors = [
        ((1, 0, 0), (1.0, 0.0, 0.0)),    # +X
        ((-1, 0, 0), (-1.0, 0.0, 0.0)),  # -X
        ((0, 1, 0), (0.0, 1.0, 0.0)),    # +Y
        ((0, -1, 0), (0.0, -1.0, 0.0)),  # -Y
        ((0, 0, 1), (0.0, 0.0, 1.0)),    # +Z
        ((0, 0, -1), (0.0, 0.0, -1.0)),  # -Z
    ]

    for (ox, oy, oz), (nx, ny, nz) in neighbors:
        check_x, check_y, check_z = x + ox, y + oy, z + oz

        # If neighbor is outside bounds or empty, this face is exposed
        if (check_x < 0 or check_x >= dx or
            check_y < 0 or check_y >= dy or
            check_z < 0 or check_z >= dz or
            (check_x, check_y, check_z) not in voxels):
            normal[0] += nx
            normal[1] += ny
            normal[2] += nz

    # Normalize
    return normalize_vector(tuple(normal))

def auto_normalize_limb(limb_data):
    """Calculate normals for all voxels in a limb."""
    voxels = limb_data['voxels']
    dims = limb_data['dims']

    new_voxels = {}
    for (x, y, z), (color, old_normal) in voxels.items():
        surface_normal = calculate_surface_normal(voxels, x, y, z, dims)
        new_normal = find_closest_normal(surface_normal)
        new_voxels[(x, y, z)] = (color, new_normal)

    return new_voxels

def write_normalized_vxl(input_path, output_path):
    """Read VXL, calculate normals, write updated file."""
    print(f"Reading: {input_path}")

    with open(input_path, 'rb') as f:
        data = bytearray(f.read())

    structure = read_vxl_structure(data)
    print(f"Found {structure['num_limbs']} limb(s)")

    # Set normals mode to 4 for all limbs
    for limb_idx in range(structure['num_limbs']):
        tailer_offset = structure['tailer_start'] + (limb_idx * 92)
        data[tailer_offset + 83] = 4  # Set normals mode

    # Read and normalize voxels
    limbs = read_vxl_voxels(bytes(data), structure)

    print("\nCalculating normals...")
    for limb_idx, limb in enumerate(limbs):
        print(f"  Processing limb {limb_idx} with {len(limb['voxels'])} voxels...")
        new_voxels = auto_normalize_limb(limb)

        # Update normal values in the file
        # This requires re-parsing and updating the span data
        # For simplicity, we update in-place where possible

        voxels_updated = 0
        dims = limb['dims']
        body_start = structure['body_start']
        tailer_offset = limb['tailer_offset']

        span_start = struct.unpack_from('<I', data, tailer_offset)[0]
        span_end = struct.unpack_from('<I', data, tailer_offset + 4)[0]
        span_data = struct.unpack_from('<I', data, tailer_offset + 8)[0]

        dim_x, dim_y, dim_z = dims

        # Re-parse spans to find voxel locations in file
        voxel_data_base = body_start + span_data

        for y in range(dim_y):
            for x in range(dim_x):
                idx = y * dim_x + x
                s_start_off = body_start + span_start + idx * 4
                s_start = struct.unpack_from('<I', data, s_start_off)[0]

                if s_start == 0xFFFFFFFF:
                    continue

                pos = voxel_data_base + s_start
                z = 0

                while z < dim_z:
                    if pos >= len(data):
                        break

                    skip = data[pos]
                    count = data[pos + 1]
                    pos += 2

                    if skip == 0 and count == 0:
                        break

                    z += skip

                    # Update normals for these voxels
                    for i in range(count):
                        vx, vy, vz = x, y, z + i
                        if (vx, vy, vz) in new_voxels:
                            color, new_normal = new_voxels[(vx, vy, vz)]
                            normal_offset = pos + i * 2 + 1
                            if normal_offset < len(data):
                                data[normal_offset] = new_normal
                                voxels_updated += 1

                    pos += count * 2
                    z += count

                    if pos < len(data):
                        end_count = data[pos]
                        pos += 1
                        z += end_count

        print(f"    Updated {voxels_updated} voxel normals")

    # Write output
    print(f"\nWriting: {output_path}")
    with open(output_path, 'wb') as f:
        f.write(data)

    print("Done!")

def main():
    if len(sys.argv) < 2:
        print("Usage: python auto_normalize_vxl.py <input.vxl> [output.vxl]")
        print("\nAuto-calculates proper lighting normals for VXL files.")
        print("If output is not specified, overwrites input file.")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path

    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    write_normalized_vxl(input_path, output_path)

if __name__ == '__main__':
    main()
