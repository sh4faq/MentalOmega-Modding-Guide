"""
Extract sample VXL/HVA files from Mental Omega MIX files for examination.
"""
import struct
import os

def read_mix_and_extract(mix_path, output_dir, max_extract=10):
    """Read MIX file and extract VXL/HVA files."""
    os.makedirs(output_dir, exist_ok=True)

    with open(mix_path, 'rb') as f:
        # Read header
        flags = struct.unpack('<I', f.read(4))[0]
        num_files = struct.unpack('<H', f.read(2))[0]
        body_size = struct.unpack('<I', f.read(4))[0]

        print(f"MIX: {os.path.basename(mix_path)}")
        print(f"Files: {num_files}, Body: {body_size} bytes")

        # Read index
        entries = []
        for i in range(num_files):
            file_id = struct.unpack('<I', f.read(4))[0]
            offset = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<I', f.read(4))[0]
            entries.append((file_id, offset, size))

        header_size = 10 + (num_files * 12)

        # Find and extract VXL/HVA files
        vxl_count = 0
        hva_count = 0

        for idx, (file_id, offset, size) in enumerate(entries):
            if vxl_count >= max_extract and hva_count >= max_extract:
                break

            f.seek(header_size + offset)
            data = f.read(size)

            # Check for VXL
            if data[:16].rstrip(b'\x00') == b'Voxel Animation':
                if vxl_count < max_extract:
                    # Get section name for filename
                    section = data[802:818].split(b'\x00')[0].decode('ascii', errors='ignore')
                    section = section.replace('/', '_').replace('\\', '_') or 'unknown'

                    out_name = f"sample_{vxl_count:02d}_{section}.vxl"
                    out_path = os.path.join(output_dir, out_name)

                    with open(out_path, 'wb') as out_f:
                        out_f.write(data)

                    print(f"  Extracted VXL: {out_name} ({size} bytes)")
                    vxl_count += 1

            # Check for HVA (by structure)
            elif len(data) >= 24:
                num_frames = struct.unpack_from('<I', data, 16)[0]
                num_sections = struct.unpack_from('<I', data, 20)[0]

                if 0 < num_frames < 500 and 0 < num_sections < 20:
                    try:
                        section_name = data[24:40].split(b'\x00')[0].decode('ascii')
                        if section_name and len(section_name) > 0 and section_name[0].isalpha():
                            if hva_count < max_extract:
                                section = section_name.replace('/', '_').replace('\\', '_')
                                out_name = f"sample_{hva_count:02d}_{section}.hva"
                                out_path = os.path.join(output_dir, out_name)

                                with open(out_path, 'wb') as out_f:
                                    out_f.write(data)

                                print(f"  Extracted HVA: {out_name} ({size} bytes, {num_frames} frames)")
                                hva_count += 1
                    except:
                        pass

        print(f"\nExtracted {vxl_count} VXL and {hva_count} HVA files to: {output_dir}")
        return vxl_count, hva_count

def analyze_vxl(filepath):
    """Detailed analysis of a VXL file."""
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"\n{'='*60}")
    print(f"VXL Analysis: {os.path.basename(filepath)}")
    print(f"{'='*60}")
    print(f"File size: {len(data)} bytes")

    # Header
    file_type = data[0:16].rstrip(b'\x00').decode('ascii')
    print(f"Type: '{file_type}'")

    unknown1 = struct.unpack_from('<I', data, 16)[0]
    num_limbs = struct.unpack_from('<I', data, 20)[0]
    num_limbs2 = struct.unpack_from('<I', data, 24)[0]
    body_size = struct.unpack_from('<I', data, 28)[0]
    palette_remap = struct.unpack_from('<H', data, 32)[0]

    print(f"Unknown1: {unknown1}")
    print(f"Num limbs: {num_limbs} (dup: {num_limbs2})")
    print(f"Body size: {body_size}")
    print(f"Palette remap start: {palette_remap}")

    # Section headers
    print(f"\nSection Headers (at offset 802):")
    for limb in range(min(num_limbs, 5)):
        offset = 802 + (limb * 28)
        section_name = data[offset:offset+16].split(b'\x00')[0].decode('ascii', errors='ignore')
        limb_num = struct.unpack_from('<I', data, offset + 16)[0]
        print(f"  Limb {limb}: name='{section_name}', num={limb_num}")

    # Tailer (dimensions)
    tailer_offset = 802 + (num_limbs * 28) + body_size
    print(f"\nTailer (at offset {tailer_offset}):")

    if tailer_offset + 92 <= len(data):
        # Read some tailer data
        dim_offset = tailer_offset + 80
        dim_x = data[dim_offset]
        dim_y = data[dim_offset + 1]
        dim_z = data[dim_offset + 2]
        normals = data[dim_offset + 3]

        print(f"  Dimensions: {dim_x} x {dim_y} x {dim_z}")
        print(f"  Normals mode: {normals}")

        # Show bounding box
        bbox_offset = tailer_offset + 36
        mins = struct.unpack_from('<3f', data, bbox_offset)
        maxs = struct.unpack_from('<3f', data, bbox_offset + 12)
        print(f"  Bounding box min: {mins}")
        print(f"  Bounding box max: {maxs}")
    else:
        print(f"  ERROR: Tailer beyond file bounds!")

    # Expected vs actual size
    expected = 34 + 768 + (num_limbs * 28) + body_size + (num_limbs * 92)
    print(f"\nExpected size: {expected} bytes")
    print(f"Actual size: {len(data)} bytes")
    print(f"Difference: {len(data) - expected} bytes")

def analyze_hva(filepath):
    """Detailed analysis of an HVA file."""
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"\n{'='*60}")
    print(f"HVA Analysis: {os.path.basename(filepath)}")
    print(f"{'='*60}")
    print(f"File size: {len(data)} bytes")

    # Header
    filename = data[0:16].rstrip(b'\x00').decode('ascii', errors='ignore')
    num_frames = struct.unpack_from('<I', data, 16)[0]
    num_sections = struct.unpack_from('<I', data, 20)[0]

    print(f"Filename/ID: '{filename}'")
    print(f"Frames: {num_frames}")
    print(f"Sections: {num_sections}")

    # Section names
    print(f"\nSection names:")
    for i in range(min(num_sections, 10)):
        offset = 24 + (i * 16)
        section_name = data[offset:offset+16].split(b'\x00')[0].decode('ascii', errors='ignore')
        print(f"  Section {i}: '{section_name}'")

    # Expected size
    expected = 24 + (num_sections * 16) + (num_frames * num_sections * 48)
    print(f"\nExpected size: {expected} bytes")
    print(f"Actual size: {len(data)} bytes")

def main():
    game_dir = r"C:\Users\hamze\Desktop\Mental Omega"
    output_dir = r"C:\Users\hamze\Desktop\MentalOmega-Modding-Guide\scripts\extracted_examples"

    # Extract from expandmo97.mix (has the MO custom units)
    mix_path = os.path.join(game_dir, "expandmo97.mix")
    if os.path.exists(mix_path):
        read_mix_and_extract(mix_path, output_dir, max_extract=5)

        # Analyze extracted files
        for f in os.listdir(output_dir):
            fpath = os.path.join(output_dir, f)
            if f.endswith('.vxl'):
                analyze_vxl(fpath)
            elif f.endswith('.hva'):
                analyze_hva(fpath)
    else:
        print(f"MIX file not found: {mix_path}")

if __name__ == "__main__":
    main()
