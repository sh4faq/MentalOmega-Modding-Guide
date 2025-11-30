"""
OBJ to VXL Converter for Red Alert 2 / Mental Omega
Converts 3D OBJ mesh files to RA2 VXL voxel format.

Usage:
    python obj_to_vxl.py input.obj output.vxl [resolution]

    resolution: Target voxel grid size (default: 40)
                Typical tank: 30-50, larger = more detail but bigger file
"""

import struct
import sys
import os
import math

def parse_obj(filepath):
    """Parse OBJ file and return vertices and faces."""
    vertices = []
    faces = []

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('v '):
                parts = line.split()
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                vertices.append((x, y, z))
            elif line.startswith('f '):
                parts = line.split()[1:]
                # Handle different face formats: v, v/vt, v/vt/vn, v//vn
                face_indices = []
                for p in parts:
                    idx = int(p.split('/')[0]) - 1  # OBJ is 1-indexed
                    face_indices.append(idx)
                # Triangulate if more than 3 vertices
                for i in range(1, len(face_indices) - 1):
                    faces.append((face_indices[0], face_indices[i], face_indices[i+1]))

    return vertices, faces

def get_bounding_box(vertices):
    """Get min/max bounds of vertices."""
    min_x = min(v[0] for v in vertices)
    max_x = max(v[0] for v in vertices)
    min_y = min(v[1] for v in vertices)
    max_y = max(v[1] for v in vertices)
    min_z = min(v[2] for v in vertices)
    max_z = max(v[2] for v in vertices)
    return (min_x, min_y, min_z), (max_x, max_y, max_z)

def normalize_vertices(vertices, target_size):
    """Normalize vertices to fit in target voxel grid size."""
    min_bound, max_bound = get_bounding_box(vertices)

    # Calculate scale to fit in target size
    size_x = max_bound[0] - min_bound[0]
    size_y = max_bound[1] - min_bound[1]
    size_z = max_bound[2] - min_bound[2]

    max_size = max(size_x, size_y, size_z)
    if max_size == 0:
        max_size = 1

    scale = (target_size - 2) / max_size  # Leave 1 voxel margin

    # Center and scale vertices
    center_x = (min_bound[0] + max_bound[0]) / 2
    center_y = (min_bound[1] + max_bound[1]) / 2
    center_z = (min_bound[2] + max_bound[2]) / 2

    normalized = []
    for x, y, z in vertices:
        nx = (x - center_x) * scale + target_size / 2
        ny = (y - center_y) * scale + target_size / 2
        nz = (z - center_z) * scale + target_size / 2
        normalized.append((nx, ny, nz))

    return normalized

def sign(p1, p2, p3):
    """Helper for point-in-triangle test."""
    return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

def point_in_triangle_2d(pt, v1, v2, v3):
    """Check if 2D point is inside triangle."""
    d1 = sign(pt, v1, v2)
    d2 = sign(pt, v2, v3)
    d3 = sign(pt, v3, v1)

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

    return not (has_neg and has_pos)

def voxelize_triangle(v1, v2, v3, voxel_grid, size_x, size_y, size_z):
    """Voxelize a single triangle into the grid."""
    # Get bounding box of triangle
    min_x = max(0, int(min(v1[0], v2[0], v3[0])))
    max_x = min(size_x - 1, int(max(v1[0], v2[0], v3[0])) + 1)
    min_y = max(0, int(min(v1[1], v2[1], v3[1])))
    max_y = min(size_y - 1, int(max(v1[1], v2[1], v3[1])) + 1)
    min_z = max(0, int(min(v1[2], v2[2], v3[2])))
    max_z = min(size_z - 1, int(max(v1[2], v2[2], v3[2])) + 1)

    # For each voxel in bounding box, check if it intersects triangle
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            for z in range(min_z, max_z + 1):
                # Simple check: if voxel center projects into triangle in XY plane
                # and Z is within range, mark as filled
                pt = (x + 0.5, y + 0.5)
                v1_2d = (v1[0], v1[1])
                v2_2d = (v2[0], v2[1])
                v3_2d = (v3[0], v3[1])

                if point_in_triangle_2d(pt, v1_2d, v2_2d, v3_2d):
                    voxel_grid[x][y][z] = True

def voxelize_mesh(vertices, faces, size):
    """Convert mesh to voxel grid."""
    # Create empty voxel grid
    voxel_grid = [[[False for _ in range(size)] for _ in range(size)] for _ in range(size)]

    # Voxelize each triangle
    for i, face in enumerate(faces):
        v1 = vertices[face[0]]
        v2 = vertices[face[1]]
        v3 = vertices[face[2]]
        voxelize_triangle(v1, v2, v3, voxel_grid, size, size, size)

        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(faces)} triangles...")

    return voxel_grid

def fill_interior(voxel_grid, size):
    """Simple interior fill using scanline in Z direction."""
    filled = [[[voxel_grid[x][y][z] for z in range(size)] for y in range(size)] for x in range(size)]

    for x in range(size):
        for y in range(size):
            inside = False
            last_was_solid = False
            for z in range(size):
                if voxel_grid[x][y][z]:
                    if not last_was_solid:
                        inside = not inside
                    last_was_solid = True
                else:
                    last_was_solid = False
                    if inside:
                        filled[x][y][z] = True

    return filled

def calculate_normals_index(x, y, z, voxel_grid, size):
    """Calculate normal direction for a voxel based on neighbors."""
    # Check which faces are exposed
    exposed = [False] * 6  # +X, -X, +Y, -Y, +Z, -Z

    if x >= size - 1 or not voxel_grid[x+1][y][z]: exposed[0] = True
    if x <= 0 or not voxel_grid[x-1][y][z]: exposed[1] = True
    if y >= size - 1 or not voxel_grid[x][y+1][z]: exposed[2] = True
    if y <= 0 or not voxel_grid[x][y-1][z]: exposed[3] = True
    if z >= size - 1 or not voxel_grid[x][y][z+1]: exposed[4] = True
    if z <= 0 or not voxel_grid[x][y][z-1]: exposed[5] = True

    # Return a normal index (simplified - using Tiberian Sun normal table)
    # TS has 36 normals, we'll use basic directions
    if exposed[4]: return 0   # Top
    if exposed[5]: return 12  # Bottom
    if exposed[0]: return 6   # +X
    if exposed[1]: return 18  # -X
    if exposed[2]: return 3   # +Y
    if exposed[3]: return 21  # -Y
    return 0

def create_vxl(voxel_grid, size_x, size_y, size_z, output_path):
    """Create VXL file from voxel grid using correct RA2 span format."""

    # Count filled voxels and find actual bounds
    actual_min_x, actual_max_x = size_x, 0
    actual_min_y, actual_max_y = size_y, 0
    actual_min_z, actual_max_z = size_z, 0

    for x in range(size_x):
        for y in range(size_y):
            for z in range(size_z):
                if voxel_grid[x][y][z]:
                    actual_min_x = min(actual_min_x, x)
                    actual_max_x = max(actual_max_x, x)
                    actual_min_y = min(actual_min_y, y)
                    actual_max_y = max(actual_max_y, y)
                    actual_min_z = min(actual_min_z, z)
                    actual_max_z = max(actual_max_z, z)

    if actual_max_x < actual_min_x:
        print("Error: No voxels generated!")
        return False

    # Actual dimensions
    dim_x = actual_max_x - actual_min_x + 1
    dim_y = actual_max_y - actual_min_y + 1
    dim_z = actual_max_z - actual_min_z + 1

    print(f"  Actual voxel dimensions: {dim_x} x {dim_y} x {dim_z}")

    # Build body data using CORRECT RA2 span format:
    # For each span: skip (1), count (1), [color, normal] * count, count (1 - duplicate!)
    # End marker: skip (1), 0 (1)
    # Empty columns use 0xFFFFFFFF as offset

    num_columns = dim_x * dim_y
    span_start_offsets = []
    span_end_offsets = []
    voxel_data = bytearray()

    for y in range(dim_y):
        for x in range(dim_x):
            src_x = x + actual_min_x
            src_y = y + actual_min_y

            # Check if column has any voxels
            has_voxels = any(voxel_grid[src_x][src_y][z + actual_min_z] for z in range(dim_z))

            if not has_voxels:
                # Empty column - use 0xFFFFFFFF
                span_start_offsets.append(0xFFFFFFFF)
                span_end_offsets.append(0xFFFFFFFF)
                continue

            col_start = len(voxel_data)
            z = 0

            while z < dim_z:
                # Find start of span (skip empty voxels)
                span_skip = z
                while z < dim_z and not voxel_grid[src_x][src_y][z + actual_min_z]:
                    z += 1

                if z >= dim_z:
                    break

                skip_count = z  # Z position where voxels start

                # Find end of span (count solid voxels)
                span_start_z = z
                while z < dim_z and voxel_grid[src_x][src_y][z + actual_min_z]:
                    z += 1
                span_count = z - span_start_z

                # Write span: skip, count, [color, normal] * count, count (duplicate!)
                voxel_data.append(skip_count)
                voxel_data.append(span_count)

                for vz in range(span_start_z, span_start_z + span_count):
                    color = 100  # Model color (green-ish from palette)
                    normal = calculate_normals_index(
                        src_x, src_y, vz + actual_min_z,
                        voxel_grid, max(size_x, size_y, size_z)
                    )
                    voxel_data.append(color)
                    voxel_data.append(normal)

                # Write count again (duplicate - required by game engine!)
                voxel_data.append(span_count)

            # Write end marker: remaining_skip, 0
            remaining = dim_z - z if z < dim_z else 0
            voxel_data.append(remaining)
            voxel_data.append(0)  # 0 voxels = end of column

            col_end = len(voxel_data)
            span_start_offsets.append(col_start)
            span_end_offsets.append(col_end)

    # Build body data with offset tables
    body_data = bytearray()

    # Span start offsets (4 bytes each)
    # Offsets are relative to span data start (after both offset tables)
    span_data_base = num_columns * 8  # Size of both offset tables
    for offset in span_start_offsets:
        if offset == 0xFFFFFFFF:
            body_data.extend(struct.pack('<I', 0xFFFFFFFF))
        else:
            body_data.extend(struct.pack('<I', offset))

    # Span end offsets (4 bytes each)
    for offset in span_end_offsets:
        if offset == 0xFFFFFFFF:
            body_data.extend(struct.pack('<I', 0xFFFFFFFF))
        else:
            body_data.extend(struct.pack('<I', offset))

    # Actual voxel span data
    body_data.extend(voxel_data)

    body_size = len(body_data)

    # Build complete VXL
    vxl_data = bytearray()

    # Header (34 bytes)
    vxl_data.extend(b'Voxel Animation\x00')  # File type (16 bytes)
    vxl_data.extend(struct.pack('<I', 1))     # Unknown = 1
    vxl_data.extend(struct.pack('<I', 1))     # Num limbs
    vxl_data.extend(struct.pack('<I', 1))     # Num limbs dup
    vxl_data.extend(struct.pack('<I', body_size))  # Body size
    vxl_data.extend(struct.pack('<H', 0))     # Palette remap

    # Palette (768 bytes)
    palette = bytearray(768)
    for i in range(256):
        if 16 <= i <= 31:
            # Team colors (will be remapped by game)
            palette[i*3:i*3+3] = [200, 0, 0]
        else:
            # Simple palette - use index 100 for model color
            if i == 100:
                palette[i*3:i*3+3] = [80, 160, 80]  # Green
            else:
                palette[i*3:i*3+3] = [i, i, i]  # Grayscale
    vxl_data.extend(palette)

    # Limb header (28 bytes)
    vxl_data.extend(b'Body\x00' + b'\x00' * 11)  # Section name (16 bytes)
    vxl_data.extend(struct.pack('<I', 0))  # Limb number
    vxl_data.extend(struct.pack('<I', 1))  # Unknown 1
    vxl_data.extend(struct.pack('<I', 2))  # Unknown 2

    # Body data
    vxl_data.extend(body_data)

    # Limb tailer (92 bytes)
    vxl_data.extend(struct.pack('<I', 0))  # Span start table offset
    vxl_data.extend(struct.pack('<I', num_columns * 4))  # Span end table offset
    vxl_data.extend(struct.pack('<I', num_columns * 8))  # Span data offset

    # Transform scale (HVA matrix multiplier) - 12 bytes (3 floats)
    scale = 0.083333  # 1/12, typical RA2 scale
    vxl_data.extend(struct.pack('<fff', scale, scale, scale))

    # Transform matrix (24 bytes - 6 floats, 2 rows of 3)
    vxl_data.extend(struct.pack('<ffffff', 1.0, 0.0, 0.0, 0.0, 1.0, 0.0))

    # Bounding box min/max (24 bytes - 6 floats)
    vxl_data.extend(struct.pack('<fff', 0.0, 0.0, 0.0))  # Min
    vxl_data.extend(struct.pack('<fff', float(dim_x), float(dim_y), float(dim_z)))  # Max

    # Padding to reach offset 88 for dimensions
    current_tailer_size = 4*3 + 4*3 + 4*6 + 4*6  # 72 bytes so far
    padding_needed = 88 - current_tailer_size
    vxl_data.extend(b'\x00' * padding_needed)

    # Dimensions at offset 88-90 from tailer start
    vxl_data.append(dim_x)
    vxl_data.append(dim_y)
    vxl_data.append(dim_z)

    # Normals mode at offset 91
    vxl_data.append(4)  # Tiberian Sun normals mode

    # Write file
    with open(output_path, 'wb') as f:
        f.write(vxl_data)

    return True

def create_hva(section_name, output_path):
    """Create matching HVA file."""
    hva_data = bytearray()

    # Header (24 bytes)
    name_bytes = os.path.splitext(os.path.basename(output_path))[0].encode('ascii')[:16]
    hva_data.extend(name_bytes.ljust(16, b'\x00'))
    hva_data.extend(struct.pack('<I', 1))  # Num frames
    hva_data.extend(struct.pack('<I', 1))  # Num sections

    # Section name (16 bytes)
    hva_data.extend(section_name.encode('ascii')[:16].ljust(16, b'\x00'))

    # Transform matrix (48 bytes - 12 floats)
    # Identity matrix
    matrix = [
        1.0, 0.0, 0.0, 0.0,  # Row 1: ScaleX, RotXY, RotXZ, TransX
        0.0, 1.0, 0.0, 0.0,  # Row 2: RotYX, ScaleY, RotYZ, TransY
        0.0, 0.0, 1.0, 0.0   # Row 3: RotZX, RotZY, ScaleZ, TransZ
    ]
    for val in matrix:
        hva_data.extend(struct.pack('<f', val))

    with open(output_path, 'wb') as f:
        f.write(hva_data)

def main():
    if len(sys.argv) < 3:
        print("Usage: python obj_to_vxl.py input.obj output.vxl [resolution]")
        print("  resolution: Target voxel grid size (default: 40)")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    resolution = int(sys.argv[3]) if len(sys.argv) > 3 else 40

    print(f"Converting {input_path} to VXL...")
    print(f"Target resolution: {resolution}")

    # Parse OBJ
    print("Parsing OBJ file...")
    vertices, faces = parse_obj(input_path)
    print(f"  Loaded {len(vertices)} vertices, {len(faces)} triangles")

    if len(vertices) == 0 or len(faces) == 0:
        print("Error: No geometry found in OBJ file!")
        sys.exit(1)

    # Normalize to fit target size
    print("Normalizing vertices...")
    vertices = normalize_vertices(vertices, resolution)

    # Voxelize
    print("Voxelizing mesh...")
    voxel_grid = voxelize_mesh(vertices, faces, resolution)

    # Optional: fill interior
    print("Filling interior...")
    voxel_grid = fill_interior(voxel_grid, resolution)

    # Count voxels
    count = sum(1 for x in range(resolution) for y in range(resolution)
                for z in range(resolution) if voxel_grid[x][y][z])
    print(f"  Total voxels: {count}")

    # Create VXL
    print("Creating VXL file...")
    if create_vxl(voxel_grid, resolution, resolution, resolution, output_path):
        print(f"  Saved: {output_path}")
    else:
        print("  Failed to create VXL!")
        sys.exit(1)

    # Create HVA
    hva_path = os.path.splitext(output_path)[0] + '.hva'
    print("Creating HVA file...")
    create_hva('Body', hva_path)
    print(f"  Saved: {hva_path}")

    print("\nDone! Files ready for Mental Omega.")
    print(f"  VXL: {output_path}")
    print(f"  HVA: {hva_path}")

if __name__ == "__main__":
    main()
