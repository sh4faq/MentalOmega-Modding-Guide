"""
VOX to VXL Converter
Converts MagicaVoxel .vox files to Red Alert 2 / Mental Omega .vxl format

Usage:
    python vox_to_vxl.py input.vox [output.vxl] [section_name]
"""

import struct
import sys
import os


def read_vox_file(filepath):
    """
    Parse MagicaVoxel .vox file format.

    Returns:
        tuple: (dimensions, voxels, palette)
        - dimensions: (x, y, z) size
        - voxels: list of (x, y, z, color_index) tuples
        - palette: list of 256 (r, g, b, a) tuples
    """
    with open(filepath, 'rb') as f:
        # Read magic number
        magic = f.read(4)
        if magic != b'VOX ':
            raise ValueError(f"Not a valid VOX file: magic={magic}")

        # Read version
        version = struct.unpack('<I', f.read(4))[0]
        print(f"VOX version: {version}")

        dimensions = None
        voxels = []
        palette = None

        # Read MAIN chunk
        main_id = f.read(4)
        if main_id != b'MAIN':
            raise ValueError(f"Expected MAIN chunk, got: {main_id}")

        main_content_size = struct.unpack('<I', f.read(4))[0]
        main_children_size = struct.unpack('<I', f.read(4))[0]

        # Read child chunks
        end_pos = f.tell() + main_children_size

        while f.tell() < end_pos:
            chunk_id = f.read(4)
            if len(chunk_id) < 4:
                break

            content_size = struct.unpack('<I', f.read(4))[0]
            children_size = struct.unpack('<I', f.read(4))[0]

            chunk_start = f.tell()

            if chunk_id == b'SIZE':
                x = struct.unpack('<I', f.read(4))[0]
                y = struct.unpack('<I', f.read(4))[0]
                z = struct.unpack('<I', f.read(4))[0]
                dimensions = (x, y, z)
                print(f"Dimensions: {x} x {y} x {z}")

            elif chunk_id == b'XYZI':
                num_voxels = struct.unpack('<I', f.read(4))[0]
                print(f"Voxel count: {num_voxels}")

                for _ in range(num_voxels):
                    vx = struct.unpack('<B', f.read(1))[0]
                    vy = struct.unpack('<B', f.read(1))[0]
                    vz = struct.unpack('<B', f.read(1))[0]
                    ci = struct.unpack('<B', f.read(1))[0]
                    voxels.append((vx, vy, vz, ci))

            elif chunk_id == b'RGBA':
                palette = []
                for i in range(256):
                    r = struct.unpack('<B', f.read(1))[0]
                    g = struct.unpack('<B', f.read(1))[0]
                    b = struct.unpack('<B', f.read(1))[0]
                    a = struct.unpack('<B', f.read(1))[0]
                    palette.append((r, g, b, a))

            # Skip to end of chunk
            f.seek(chunk_start + content_size + children_size)

        # Default palette if none found
        if palette is None:
            palette = [(i, i, i, 255) for i in range(256)]

        return dimensions, voxels, palette


def voxels_to_grid(dimensions, voxels):
    """Convert voxel list to 3D grid with color indices."""
    dim_x, dim_y, dim_z = dimensions

    # Create empty grid (0 = empty)
    grid = [[[0 for _ in range(dim_z)] for _ in range(dim_y)] for _ in range(dim_x)]

    for x, y, z, color in voxels:
        if 0 <= x < dim_x and 0 <= y < dim_y and 0 <= z < dim_z:
            grid[x][y][z] = color

    return grid


def calculate_normal_index(x, y, z, grid, dim_x, dim_y, dim_z):
    """Calculate RA2 normal index based on exposed faces."""
    exposed = [False] * 6

    # Check which faces are exposed
    if x >= dim_x - 1 or grid[x+1][y][z] == 0: exposed[0] = True  # +X
    if x <= 0 or grid[x-1][y][z] == 0: exposed[1] = True          # -X
    if y >= dim_y - 1 or grid[x][y+1][z] == 0: exposed[2] = True  # +Y
    if y <= 0 or grid[x][y-1][z] == 0: exposed[3] = True          # -Y
    if z >= dim_z - 1 or grid[x][y][z+1] == 0: exposed[4] = True  # +Z (top)
    if z <= 0 or grid[x][y][z-1] == 0: exposed[5] = True          # -Z (bottom)

    # RA2 normal indices (Tiberian Sun style = mode 2)
    if exposed[4]: return 0   # Top
    if exposed[5]: return 12  # Bottom
    if exposed[0]: return 6   # +X
    if exposed[1]: return 18  # -X
    if exposed[2]: return 3   # +Y
    if exposed[3]: return 21  # -Y
    return 0


def map_color_to_ra2(color_index, vox_palette):
    """
    Map MagicaVoxel color to RA2 palette index.

    Keep the original color index - the palette will be written to VXL file.
    Avoid indices 16-31 which are reserved for team colors.
    """
    if color_index == 0:
        return 0

    # Keep original index, but shift if it falls in team color range (16-31)
    if 16 <= color_index <= 31:
        return color_index + 32  # Shift to safe range

    return color_index


def create_vxl_from_grid(grid, dim_x, dim_y, dim_z, vox_palette, section_name="Body"):
    """
    Create VXL file data from voxel grid.

    Format based on working wrmn.vxl analysis.
    """
    # Build span data
    num_columns = dim_x * dim_y
    span_start_offsets = []
    span_end_offsets = []
    voxel_data = bytearray()

    filled_count = 0

    for y in range(dim_y):
        for x in range(dim_x):
            has_voxels = any(grid[x][y][z] != 0 for z in range(dim_z))

            if not has_voxels:
                span_start_offsets.append(0xFFFFFFFF)
                span_end_offsets.append(0xFFFFFFFF)
                continue

            col_start = len(voxel_data)
            z = 0
            last_span_end_z = 0  # Track where the last span ended

            while z < dim_z:
                # Skip empty voxels
                while z < dim_z and grid[x][y][z] == 0:
                    z += 1
                if z >= dim_z:
                    break

                # Skip count is RELATIVE to end of previous span, not absolute!
                skip_count = z - last_span_end_z

                # Count solid voxels in this span
                span_start_z = z
                while z < dim_z and grid[x][y][z] != 0:
                    z += 1
                span_count = z - span_start_z
                last_span_end_z = z  # Update last span end position

                # Write span header: skip, count
                voxel_data.append(skip_count)
                voxel_data.append(span_count)

                # Write voxel data: [color, normal] * count
                for vz in range(span_start_z, span_start_z + span_count):
                    color = map_color_to_ra2(grid[x][y][vz], vox_palette)
                    normal = calculate_normal_index(x, y, vz, grid, dim_x, dim_y, dim_z)
                    voxel_data.append(color)
                    voxel_data.append(normal)
                    filled_count += 1

                # Duplicate count (REQUIRED by game engine!)
                voxel_data.append(span_count)

            # End marker: remaining voxels above the last span
            remaining = dim_z - last_span_end_z
            voxel_data.append(remaining)
            voxel_data.append(0)

            col_end = len(voxel_data)
            span_start_offsets.append(col_start)
            span_end_offsets.append(col_end)

    print(f"Filled voxels: {filled_count}")

    # Build body data (offsets + voxel data)
    body_data = bytearray()

    # Span start offsets (4 bytes each)
    for offset in span_start_offsets:
        body_data.extend(struct.pack('<I', offset))

    # Span end offsets (4 bytes each)
    for offset in span_end_offsets:
        body_data.extend(struct.pack('<I', offset))

    # Voxel span data
    body_data.extend(voxel_data)
    body_size = len(body_data)

    # === Build complete VXL file ===
    vxl_data = bytearray()

    # --- Header (32 bytes) ---
    vxl_data.extend(b'Voxel Animation\x00')  # 16 bytes: file type
    vxl_data.extend(struct.pack('<I', 1))     # 4 bytes: unknown (always 1)
    vxl_data.extend(struct.pack('<I', 1))     # 4 bytes: num limbs
    vxl_data.extend(struct.pack('<I', 1))     # 4 bytes: num limbs (duplicate)
    vxl_data.extend(struct.pack('<I', body_size))  # 4 bytes: body size

    # --- Remap indices (2 bytes, at offset 32) ---
    vxl_data.append(16)  # Remap start index (team color palette start)
    vxl_data.append(31)  # Remap end index (team color palette end)

    # --- Palette (768 bytes, starts at offset 34) ---
    # Write actual colors from VOX palette
    # VOX uses 1-indexed colors: voxel color N uses palette[N-1]
    # VXL palette index 0 is unused, index N should have color for voxels with color N
    for i in range(256):
        if i == 0:
            # Index 0 is unused - write black
            vxl_data.extend(bytes([0, 0, 0]))
        elif i - 1 < len(vox_palette):
            # Shift by 1: VXL palette[N] = VOX palette[N-1]
            r, g, b, a = vox_palette[i - 1]
            vxl_data.extend(bytes([r, g, b]))
        else:
            vxl_data.extend(bytes([128, 128, 128]))  # Fallback gray

    # --- Limb Header (28 bytes, starts at offset 802) ---
    name_bytes = section_name.encode('ascii')[:16].ljust(16, b'\x00')
    vxl_data.extend(name_bytes)           # 16 bytes: section name
    vxl_data.extend(struct.pack('<I', 0)) # 4 bytes: limb number (0)
    vxl_data.extend(struct.pack('<I', 1)) # 4 bytes: unknown1 (1)
    vxl_data.extend(struct.pack('<I', 0)) # 4 bytes: unknown2 (0)

    # --- Body Data (variable) ---
    vxl_data.extend(body_data)

    # --- Tailer (92 bytes) ---
    # Offsets into body data
    vxl_data.extend(struct.pack('<I', 0))                    # Span start offset (0)
    vxl_data.extend(struct.pack('<I', num_columns * 4))      # Span end offset
    vxl_data.extend(struct.pack('<I', num_columns * 8))      # Span data offset

    # Scale (0.083333 = 1/12, standard for RA2)
    vxl_data.extend(struct.pack('<f', 0.083333))

    # Transform matrix (identity, 12 floats = 48 bytes)
    for val in [1.0, 0.0, 0.0, 0.0,   # Row 1
                0.0, 1.0, 0.0, 0.0,   # Row 2
                0.0, 0.0, 1.0, 0.0]:  # Row 3
        vxl_data.extend(struct.pack('<f', val))

    # Calculate bounds based on dimensions
    scale = 0.083333
    min_bounds = (-(dim_x / 2.0) / scale, -(dim_y / 2.0) / scale, 0.0)
    max_bounds = ((dim_x / 2.0) / scale, (dim_y / 2.0) / scale, dim_z / scale)

    # MinBounds (3 floats = 12 bytes)
    vxl_data.extend(struct.pack('<fff', min_bounds[0], min_bounds[1], min_bounds[2]))

    # MaxBounds (3 floats = 12 bytes)
    vxl_data.extend(struct.pack('<fff', max_bounds[0], max_bounds[1], max_bounds[2]))

    # Dimensions (3 bytes)
    vxl_data.append(dim_x)
    vxl_data.append(dim_y)
    vxl_data.append(dim_z)

    # Normals mode (1 byte) - 2 = Tiberian Sun, 4 = Red Alert 2
    vxl_data.append(4)

    return bytes(vxl_data), name_bytes


def create_hva(section_name_bytes, filename="EXPORT"):
    """
    Create HVA file with matching section name.

    Format: 88 bytes total
    - Header: 24 bytes (filename + frame count + section count)
    - Section name: 16 bytes (MUST match VXL)
    - Transform matrix: 48 bytes (identity)
    """
    hva_data = bytearray()

    # Header (24 bytes)
    hva_data.extend(filename.encode('ascii')[:16].ljust(16, b'\x00'))
    hva_data.extend(struct.pack('<I', 1))  # 1 frame
    hva_data.extend(struct.pack('<I', 1))  # 1 section

    # Section name (16 bytes) - MUST match VXL
    hva_data.extend(section_name_bytes)

    # Transform matrix (48 bytes) - identity
    for val in [1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0]:
        hva_data.extend(struct.pack('<f', val))

    return bytes(hva_data)


def convert_vox_to_vxl(input_path, output_path=None, section_name="Body"):
    """
    Convert MagicaVoxel .vox to RA2 .vxl format.

    Args:
        input_path: Path to .vox file
        output_path: Path for output .vxl file (default: same name with .vxl extension)
        section_name: VXL section name (default: "Body")
    """
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + '.vxl'

    print(f"Converting: {input_path}")
    print(f"Output: {output_path}")
    print(f"Section: {section_name}")
    print("-" * 50)

    # Read VOX file
    dimensions, voxels, palette = read_vox_file(input_path)

    if dimensions is None:
        raise ValueError("No SIZE chunk found in VOX file")

    dim_x, dim_y, dim_z = dimensions

    # Convert to grid
    grid = voxels_to_grid(dimensions, voxels)

    # Create VXL
    vxl_data, section_name_bytes = create_vxl_from_grid(
        grid, dim_x, dim_y, dim_z, palette, section_name
    )

    # Write VXL
    with open(output_path, 'wb') as f:
        f.write(vxl_data)

    print(f"VXL size: {len(vxl_data)} bytes")

    # Create HVA
    hva_path = os.path.splitext(output_path)[0] + '.hva'
    basename = os.path.splitext(os.path.basename(output_path))[0].upper()
    hva_data = create_hva(section_name_bytes, basename)

    with open(hva_path, 'wb') as f:
        f.write(hva_data)

    print(f"HVA size: {len(hva_data)} bytes")
    print(f"HVA path: {hva_path}")
    print("-" * 50)
    print("Conversion complete!")

    return output_path, hva_path


def main():
    if len(sys.argv) < 2:
        print("VOX to VXL Converter")
        print("=" * 50)
        print("\nUsage:")
        print("  python vox_to_vxl.py input.vox [output.vxl] [section_name]")
        print("\nExamples:")
        print("  python vox_to_vxl.py tank.vox")
        print("  python vox_to_vxl.py tank.vox FTNKNEXUS.vxl")
        print("  python vox_to_vxl.py tank.vox FTNKNEXUS.vxl Body")
        return

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    section_name = sys.argv[3] if len(sys.argv) > 3 else "Body"

    convert_vox_to_vxl(input_path, output_path, section_name)


if __name__ == "__main__":
    main()
