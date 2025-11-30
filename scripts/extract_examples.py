"""
Extract VXL/HVA examples from Mental Omega MIX files.
Since MIX files don't store filenames (only hashes), we identify files by content.
"""
import struct
import os
import sys

# Known unit names to search for (we'll calculate their IDs)
KNOWN_UNITS = [
    # Allied tanks
    "MTNK", "HTNK", "SREF", "CTNK", "TNKD",
    # Soviet tanks
    "HOWI", "RHNO", "APOC", "TTNK", "DESO",
    # Epsilon
    "DVST", "MAGS", "GATS", "MIND",
    # Common turrets
    "MTNKTUR", "HTNKTUR", "APOCTUR", "RHNOTUR",
]

def calculate_file_id(filename):
    """Generate Westwood-style file ID from filename."""
    name = filename.upper()
    file_id = 0
    for char in name:
        file_id = ((file_id << 1) | (file_id >> 31)) + ord(char)
        file_id &= 0xFFFFFFFF
    return file_id

def read_mix_index(filepath):
    """Read MIX file and return index entries with file data."""
    with open(filepath, 'rb') as f:
        # Read header
        flags = struct.unpack('<I', f.read(4))[0]

        # Check for encryption flag
        if flags & 0x00020000:
            print(f"  Warning: MIX file appears to have special flags: 0x{flags:08X}")

        num_files = struct.unpack('<H', f.read(2))[0]
        body_size = struct.unpack('<I', f.read(4))[0]

        # Read index entries
        entries = []
        for i in range(num_files):
            file_id = struct.unpack('<I', f.read(4))[0]
            offset = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<I', f.read(4))[0]
            entries.append({'id': file_id, 'offset': offset, 'size': size})

        # Calculate body start position
        header_size = 10 + (num_files * 12)

        return {
            'flags': flags,
            'num_files': num_files,
            'body_size': body_size,
            'body_start': header_size,
            'entries': entries,
            'filepath': filepath
        }

def extract_file_from_mix(mix_info, entry_idx, output_path):
    """Extract a specific file from MIX by index."""
    entry = mix_info['entries'][entry_idx]

    with open(mix_info['filepath'], 'rb') as f:
        f.seek(mix_info['body_start'] + entry['offset'])
        data = f.read(entry['size'])

    with open(output_path, 'wb') as f:
        f.write(data)

    return data

def identify_file_type(data):
    """Identify file type from content."""
    if len(data) < 20:
        return "unknown", {}

    # Check for VXL (starts with "Voxel Animation")
    if data[:16].rstrip(b'\x00') == b'Voxel Animation':
        num_limbs = struct.unpack_from('<I', data, 20)[0]
        body_size = struct.unpack_from('<I', data, 28)[0]

        # Try to get section name
        section_name = ""
        if len(data) > 818:
            section_name = data[802:818].split(b'\x00')[0].decode('ascii', errors='ignore')

        # Try to get dimensions
        dims = (0, 0, 0)
        try:
            tailer_offset = 802 + (num_limbs * 28) + body_size
            if tailer_offset + 83 <= len(data):
                dims = (data[tailer_offset + 80], data[tailer_offset + 81], data[tailer_offset + 82])
        except:
            pass

        return "VXL", {
            'limbs': num_limbs,
            'body_size': body_size,
            'section': section_name,
            'dimensions': dims
        }

    # Check for HVA
    if len(data) >= 24:
        num_frames = struct.unpack_from('<I', data, 16)[0]
        num_sections = struct.unpack_from('<I', data, 20)[0]

        # HVA validation: reasonable frame/section counts
        if 0 < num_frames < 1000 and 0 < num_sections < 50:
            # Check if section name area looks like text
            if len(data) > 40:
                section_data = data[24:40]
                # If first section name looks like ASCII text, probably HVA
                try:
                    section_name = section_data.split(b'\x00')[0].decode('ascii')
                    if section_name and section_name.isprintable():
                        return "HVA", {
                            'frames': num_frames,
                            'sections': num_sections,
                            'section_name': section_name
                        }
                except:
                    pass

    # Check for SHP (cameo icons, etc.)
    if len(data) >= 8:
        # SHP files start with frame count (usually small number)
        possible_frames = struct.unpack_from('<H', data, 0)[0]
        if 1 <= possible_frames <= 500:
            # Could be SHP - check for reasonable dimensions
            if len(data) >= 14:
                width = struct.unpack_from('<H', data, 6)[0]
                height = struct.unpack_from('<H', data, 8)[0]
                if 0 < width <= 500 and 0 < height <= 500:
                    return "SHP", {'frames': possible_frames, 'width': width, 'height': height}

    return "unknown", {}

def scan_mix_for_vxl(mix_path, output_dir=None):
    """Scan a MIX file and identify/extract VXL files."""
    print(f"\n{'='*60}")
    print(f"Scanning: {os.path.basename(mix_path)}")
    print(f"{'='*60}")

    try:
        mix_info = read_mix_index(mix_path)
    except Exception as e:
        print(f"  Error reading MIX: {e}")
        return []

    print(f"  Flags: 0x{mix_info['flags']:08X}")
    print(f"  Files: {mix_info['num_files']}")
    print(f"  Body size: {mix_info['body_size']} bytes")

    # Build lookup table for known unit names
    known_ids = {}
    for unit in KNOWN_UNITS:
        for ext in ['.vxl', '.hva', '.VXL', '.HVA']:
            name = unit + ext
            known_ids[calculate_file_id(name)] = name

    vxl_files = []
    hva_files = []
    shp_files = []

    with open(mix_path, 'rb') as f:
        for idx, entry in enumerate(mix_info['entries']):
            # Read file data
            f.seek(mix_info['body_start'] + entry['offset'])
            data = f.read(min(entry['size'], 2000))  # Read first 2KB for identification

            file_type, info = identify_file_type(data)

            # Check if this is a known file
            known_name = known_ids.get(entry['id'], None)

            if file_type == "VXL":
                vxl_files.append({
                    'idx': idx,
                    'id': entry['id'],
                    'size': entry['size'],
                    'known_name': known_name,
                    'info': info
                })
            elif file_type == "HVA":
                hva_files.append({
                    'idx': idx,
                    'id': entry['id'],
                    'size': entry['size'],
                    'known_name': known_name,
                    'info': info
                })
            elif file_type == "SHP":
                shp_files.append({
                    'idx': idx,
                    'id': entry['id'],
                    'size': entry['size'],
                    'known_name': known_name,
                    'info': info
                })

    print(f"\n  Found: {len(vxl_files)} VXL, {len(hva_files)} HVA, {len(shp_files)} SHP files")

    # Print VXL details
    if vxl_files:
        print(f"\n  VXL Files:")
        for vxl in vxl_files[:10]:  # Show first 10
            name = vxl['known_name'] or f"ID_0x{vxl['id']:08X}"
            dims = vxl['info'].get('dimensions', (0,0,0))
            section = vxl['info'].get('section', '?')
            print(f"    {name:20} {vxl['size']:>8} bytes  dims={dims[0]}x{dims[1]}x{dims[2]}  section='{section}'")
        if len(vxl_files) > 10:
            print(f"    ... and {len(vxl_files) - 10} more")

    return vxl_files + hva_files

def extract_examples(game_dir, output_dir):
    """Extract example VXL/HVA files from game MIX files."""
    os.makedirs(output_dir, exist_ok=True)

    # MIX files to scan (in priority order)
    mix_files = [
        'ra2md.mix',      # Main YR assets
        'expandmd01.mix', # Expansion assets
        'expandmo97.mix', # MO assets
        'expandmo99.mix', # MO assets
        'cache.mix',
        'cachemd.mix',
    ]

    all_assets = []

    for mix_name in mix_files:
        mix_path = os.path.join(game_dir, mix_name)
        if os.path.exists(mix_path):
            assets = scan_mix_for_vxl(mix_path, output_dir)
            all_assets.extend(assets)

    print(f"\n{'='*60}")
    print(f"Total assets found: {len(all_assets)}")
    print(f"{'='*60}")

def main():
    if len(sys.argv) >= 2:
        game_dir = sys.argv[1]
    else:
        game_dir = r"C:\Users\hamze\Desktop\Mental Omega"

    output_dir = os.path.join(os.path.dirname(__file__), "extracted_examples")

    print(f"Game directory: {game_dir}")
    print(f"Output directory: {output_dir}")

    extract_examples(game_dir, output_dir)

if __name__ == "__main__":
    main()
