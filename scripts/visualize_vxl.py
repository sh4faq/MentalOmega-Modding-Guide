"""
Visualize VXL file structure and create a text-based representation.
Also search for and display info about game cameos (unit icons).
"""
import struct
import os

def hex_dump(data, start, length, cols=16):
    """Create a hex dump of data."""
    lines = []
    for i in range(0, length, cols):
        offset = start + i
        hex_part = ' '.join(f'{data[start+i+j]:02X}' for j in range(min(cols, length-i)))
        ascii_part = ''.join(chr(data[start+i+j]) if 32 <= data[start+i+j] < 127 else '.'
                            for j in range(min(cols, length-i)))
        lines.append(f'{offset:08X}: {hex_part:<48} {ascii_part}')
    return '\n'.join(lines)

def visualize_vxl_structure(filepath):
    """Create a visual representation of VXL file structure."""
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"\n{'='*70}")
    print(f"VXL FILE: {os.path.basename(filepath)}")
    print(f"{'='*70}")

    # Header visualization
    print("\n[HEADER] Offset 0x0000, Size: 34 bytes")
    print("-" * 70)
    print(hex_dump(data, 0, 34))

    file_type = data[0:16].rstrip(b'\x00').decode('ascii')
    num_limbs = struct.unpack_from('<I', data, 20)[0]
    body_size = struct.unpack_from('<I', data, 28)[0]

    print(f"\n  Decoded:")
    print(f"    File type: '{file_type}'")
    print(f"    Limbs: {num_limbs}")
    print(f"    Body size: {body_size} bytes")

    # Palette (just show it exists)
    print(f"\n[PALETTE] Offset 0x0022 (34), Size: 768 bytes (256 RGB colors)")
    print("-" * 70)
    print(f"  First 16 colors (hex dump of first 48 bytes):")
    print(hex_dump(data, 34, 48))

    # Section header
    section_offset = 802
    print(f"\n[SECTION HEADERS] Offset 0x{section_offset:04X} ({section_offset}), Size: {num_limbs * 28} bytes")
    print("-" * 70)
    for i in range(min(num_limbs, 3)):
        off = section_offset + (i * 28)
        print(f"\n  Limb {i} header (28 bytes):")
        print(hex_dump(data, off, 28))
        section_name = data[off:off+16].split(b'\x00')[0].decode('ascii', errors='ignore')
        print(f"    Section name: '{section_name}'")

    # Body data
    body_offset = section_offset + (num_limbs * 28)
    print(f"\n[BODY DATA] Offset 0x{body_offset:04X} ({body_offset}), Size: {body_size} bytes")
    print("-" * 70)
    print(f"  First 64 bytes of voxel data:")
    print(hex_dump(data, body_offset, min(64, body_size)))
    print(f"  ... ({body_size - 64} more bytes) ...")

    # Tailer
    tailer_offset = body_offset + body_size
    print(f"\n[TAILER] Offset 0x{tailer_offset:04X} ({tailer_offset}), Size: 92 bytes per limb")
    print("-" * 70)
    print(f"  Tailer hex dump:")
    print(hex_dump(data, tailer_offset, min(92, len(data) - tailer_offset)))

    # Dimensions are at offset 80-82 within tailer
    if tailer_offset + 83 <= len(data):
        dim_x = data[tailer_offset + 80]
        dim_y = data[tailer_offset + 81]
        dim_z = data[tailer_offset + 82]
        print(f"\n  Dimensions (at tailer+80): {dim_x} x {dim_y} x {dim_z}")

    print(f"\n[SUMMARY]")
    print(f"  Total file size: {len(data)} bytes")
    print(f"  Structure: Header(34) + Palette(768) + SectionHeaders({num_limbs}*28={num_limbs*28}) + Body({body_size}) + Tailers({num_limbs}*92={num_limbs*92})")
    expected = 34 + 768 + (num_limbs * 28) + body_size + (num_limbs * 92)
    print(f"  Expected: {expected} bytes")

def visualize_hva_structure(filepath):
    """Create a visual representation of HVA file structure."""
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"\n{'='*70}")
    print(f"HVA FILE: {os.path.basename(filepath)}")
    print(f"{'='*70}")

    # Header
    print("\n[HEADER] Offset 0x0000, Size: 24 bytes")
    print("-" * 70)
    print(hex_dump(data, 0, 24))

    filename = data[0:16].rstrip(b'\x00').decode('ascii', errors='ignore')
    num_frames = struct.unpack_from('<I', data, 16)[0]
    num_sections = struct.unpack_from('<I', data, 20)[0]

    print(f"\n  Decoded:")
    print(f"    Filename: '{filename}'")
    print(f"    Frames: {num_frames}")
    print(f"    Sections: {num_sections}")

    # Section names
    print(f"\n[SECTION NAMES] Offset 0x0018 (24), Size: {num_sections * 16} bytes")
    print("-" * 70)
    for i in range(min(num_sections, 5)):
        off = 24 + (i * 16)
        section_name = data[off:off+16].split(b'\x00')[0].decode('ascii', errors='ignore')
        print(f"  Section {i}: '{section_name}'")
        print(hex_dump(data, off, 16))

    # Transform matrices
    matrix_offset = 24 + (num_sections * 16)
    print(f"\n[TRANSFORM MATRICES] Offset 0x{matrix_offset:04X} ({matrix_offset})")
    print("-" * 70)
    print(f"  Each frame has {num_sections} section(s) x 48 bytes (3x4 float matrix)")

    if matrix_offset + 48 <= len(data):
        print(f"\n  First matrix (frame 0, section 0):")
        print(hex_dump(data, matrix_offset, 48))

        # Decode matrix
        matrix = struct.unpack_from('<12f', data, matrix_offset)
        print(f"\n  Decoded 3x4 matrix:")
        print(f"    [{matrix[0]:8.4f} {matrix[1]:8.4f} {matrix[2]:8.4f} {matrix[3]:8.4f}]")
        print(f"    [{matrix[4]:8.4f} {matrix[5]:8.4f} {matrix[6]:8.4f} {matrix[7]:8.4f}]")
        print(f"    [{matrix[8]:8.4f} {matrix[9]:8.4f} {matrix[10]:8.4f} {matrix[11]:8.4f}]")

    print(f"\n[SUMMARY]")
    print(f"  Total file size: {len(data)} bytes")
    expected = 24 + (num_sections * 16) + (num_frames * num_sections * 48)
    print(f"  Expected: {expected} bytes")

def main():
    example_dir = r"C:\Users\hamze\Desktop\MentalOmega-Modding-Guide\scripts\extracted_examples"

    # Visualize one VXL and one HVA
    for f in os.listdir(example_dir):
        fpath = os.path.join(example_dir, f)
        if f.endswith('.vxl') and 'Body' in f:
            visualize_vxl_structure(fpath)
            break

    for f in os.listdir(example_dir):
        fpath = os.path.join(example_dir, f)
        if f.endswith('.hva') and 'Body' in f:
            visualize_hva_structure(fpath)
            break

if __name__ == "__main__":
    main()
