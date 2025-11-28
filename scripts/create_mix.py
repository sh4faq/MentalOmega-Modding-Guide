"""
MIX File Creator for Mental Omega / Red Alert 2 / Yuri's Revenge
Creates unencrypted MIX archives compatible with the Westwood game engine.

Usage:
    python create_mix.py output.mix file1.vxl file2.hva ...
    python create_mix.py  # Uses default configuration below
"""
import struct
import os
import sys
import glob


def calculate_file_id(filename):
    """
    Generate Westwood-style file ID from filename.
    This is a CRC-like hash used by the game to look up files.
    """
    name = filename.upper()
    file_id = 0
    for char in name:
        file_id = ((file_id << 1) | (file_id >> 31)) + ord(char)
        file_id &= 0xFFFFFFFF  # Keep as 32-bit unsigned
    return file_id


def create_mix(output_path, files):
    """
    Create a MIX file from a list of file paths.

    Args:
        output_path: Path for the output MIX file
        files: List of file paths to include in the MIX

    The MIX format:
        - 4 bytes: Flags (0 = unencrypted)
        - 2 bytes: Number of files
        - 4 bytes: Total body size
        - N * 12 bytes: Index entries (ID, offset, size)
        - Body: Raw file data concatenated
    """
    # Read all file contents and calculate IDs
    file_data = []
    for filepath in files:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            data = f.read()

        file_id = calculate_file_id(filename)
        file_data.append((file_id, filename, data))

    # Sort by ID (REQUIRED by MIX format for binary search)
    file_data.sort(key=lambda x: x[0])

    # Calculate offsets and total body size
    num_files = len(file_data)
    current_offset = 0
    index_entries = []
    body_size = 0

    for file_id, filename, data in file_data:
        size = len(data)
        index_entries.append((file_id, current_offset, size))
        current_offset += size
        body_size += size

    # Write the MIX file
    with open(output_path, 'wb') as f:
        # Header
        f.write(struct.pack('<I', 0))         # Flags: 0 = no encryption, no checksum
        f.write(struct.pack('<H', num_files)) # Number of files (16-bit)
        f.write(struct.pack('<I', body_size)) # Total body size (32-bit)

        # Index entries (must be sorted by file ID)
        for file_id, offset, size in index_entries:
            f.write(struct.pack('<I', file_id))  # File ID
            f.write(struct.pack('<I', offset))   # Offset in body section
            f.write(struct.pack('<I', size))     # File size

        # File bodies
        for file_id, filename, data in file_data:
            f.write(data)

    # Print summary
    print(f"Created: {output_path}")
    print(f"Total size: {os.path.getsize(output_path)} bytes")
    print(f"Contains {num_files} file(s):")
    print("-" * 50)

    for file_id, filename, data in file_data:
        print(f"  {filename:24} ID: 0x{file_id:08X}  Size: {len(data):>8} bytes")

    print("-" * 50)


def read_mix(filepath):
    """
    Read and display contents of a MIX file.
    Useful for verification.
    """
    with open(filepath, 'rb') as f:
        # Read header
        flags = struct.unpack('<I', f.read(4))[0]
        num_files = struct.unpack('<H', f.read(2))[0]
        body_size = struct.unpack('<I', f.read(4))[0]

        print(f"MIX File: {filepath}")
        print(f"Flags: {flags} {'(encrypted)' if flags else '(unencrypted)'}")
        print(f"Files: {num_files}")
        print(f"Body size: {body_size} bytes")
        print("-" * 50)

        # Read index entries
        entries = []
        for i in range(num_files):
            file_id = struct.unpack('<I', f.read(4))[0]
            offset = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<I', f.read(4))[0]
            entries.append((file_id, offset, size))
            print(f"  [{i:2}] ID: 0x{file_id:08X}  Offset: {offset:>8}  Size: {size:>8}")

        print("-" * 50)
        return entries


def main():
    if len(sys.argv) >= 3:
        # Command line mode: create_mix.py output.mix file1 file2 ...
        output_file = sys.argv[1]
        input_files = sys.argv[2:]

        # Expand wildcards
        expanded_files = []
        for pattern in input_files:
            matches = glob.glob(pattern)
            if matches:
                expanded_files.extend(matches)
            else:
                expanded_files.append(pattern)

        create_mix(output_file, expanded_files)

    elif len(sys.argv) == 2:
        # Read mode: create_mix.py existing.mix
        if sys.argv[1].endswith('.mix'):
            read_mix(sys.argv[1])
        else:
            print("Usage:")
            print("  python create_mix.py output.mix file1.vxl file2.hva ...")
            print("  python create_mix.py existing.mix  # Read contents")

    else:
        # Default mode: look for VXL/HVA files in current directory
        print("=" * 60)
        print("MIX File Creator")
        print("=" * 60)

        # Find all VXL and HVA files
        vxl_files = glob.glob("*.vxl") + glob.glob("*.VXL")
        hva_files = glob.glob("*.hva") + glob.glob("*.HVA")
        all_files = sorted(set(vxl_files + hva_files))

        if not all_files:
            print("\nNo VXL/HVA files found in current directory.")
            print("\nUsage:")
            print("  python create_mix.py output.mix file1.vxl file2.hva ...")
            print("  python create_mix.py existing.mix  # Read existing MIX")
            return

        print(f"\nFound {len(all_files)} file(s) to pack:")
        for f in all_files:
            print(f"  {f}")

        output_file = "expandmo02.mix"
        print(f"\nCreating: {output_file}")
        print()

        create_mix(output_file, all_files)

        print(f"\nDone! Copy {output_file} to your Mental Omega folder.")


if __name__ == "__main__":
    main()
