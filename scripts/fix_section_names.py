"""
Fix VXL/HVA Section Name Mismatch
Ensures VXL and HVA section names match for proper animation.

Usage:
    python fix_section_names.py                    # Interactive mode
    python fix_section_names.py body.vxl body.hva  # Fix specific pair
"""
import struct
import os
import sys
import shutil


def get_vxl_section_name(filepath):
    """Extract the first section name from a VXL file."""
    with open(filepath, 'rb') as f:
        f.seek(802)  # Section name starts at offset 802
        name = f.read(16).split(b'\x00')[0]
    return name.decode('ascii', errors='replace')


def get_hva_section_name(filepath):
    """Extract the first section name from an HVA file."""
    with open(filepath, 'rb') as f:
        f.seek(24)  # Section name starts at offset 24
        name = f.read(16).split(b'\x00')[0]
    return name.decode('ascii', errors='replace')


def set_vxl_section_name(filepath, new_name, backup=True):
    """Set the section name in a VXL file."""
    if backup:
        backup_path = filepath + '.backup'
        if not os.path.exists(backup_path):
            shutil.copy(filepath, backup_path)
            print(f"  Backed up to: {backup_path}")

    with open(filepath, 'rb') as f:
        data = bytearray(f.read())

    # Create new padded section name (16 bytes)
    new_bytes = new_name.encode('ascii')[:16].ljust(16, b'\x00')
    data[802:818] = new_bytes

    with open(filepath, 'wb') as f:
        f.write(data)

    print(f"  Set VXL section name to: '{new_name}'")


def set_hva_section_name(filepath, new_name, backup=True):
    """Set the section name in an HVA file."""
    if backup:
        backup_path = filepath + '.backup'
        if not os.path.exists(backup_path):
            shutil.copy(filepath, backup_path)
            print(f"  Backed up to: {backup_path}")

    with open(filepath, 'rb') as f:
        data = bytearray(f.read())

    # Create new padded section name (16 bytes)
    new_bytes = new_name.encode('ascii')[:16].ljust(16, b'\x00')
    data[24:40] = new_bytes

    with open(filepath, 'wb') as f:
        f.write(data)

    print(f"  Set HVA section name to: '{new_name}'")


def fix_pair(vxl_path, hva_path, target_name=None):
    """Fix a VXL/HVA pair to have matching section names."""
    print(f"\nProcessing: {os.path.basename(vxl_path)} + {os.path.basename(hva_path)}")

    vxl_name = get_vxl_section_name(vxl_path)
    hva_name = get_hva_section_name(hva_path)

    print(f"  Current VXL section: '{vxl_name}'")
    print(f"  Current HVA section: '{hva_name}'")

    if vxl_name == hva_name:
        print("  Already matching - no changes needed.")
        return

    # Determine target name
    if target_name is None:
        # Use VXL name by default, or prompt
        if vxl_name in ['body', 'turret', 'barrel']:
            target_name = vxl_name
        elif hva_name in ['body', 'turret', 'barrel']:
            target_name = hva_name
        else:
            # Default to 'body' for body files, 'turret' for turret files
            basename = os.path.basename(vxl_path).upper()
            if 'TUR' in basename:
                target_name = 'turret'
            elif 'BARL' in basename or 'BAR' in basename:
                target_name = 'barrel'
            else:
                target_name = 'body'

    print(f"  Target section name: '{target_name}'")

    # Fix both files
    if vxl_name != target_name:
        set_vxl_section_name(vxl_path, target_name)

    if hva_name != target_name:
        set_hva_section_name(hva_path, target_name)

    print("  Fixed!")


def find_pairs(directory='.'):
    """Find VXL/HVA pairs in directory."""
    vxl_files = {}
    hva_files = {}

    for f in os.listdir(directory):
        name, ext = os.path.splitext(f)
        ext = ext.lower()
        path = os.path.join(directory, f)

        if ext == '.vxl':
            vxl_files[name.upper()] = path
        elif ext == '.hva':
            hva_files[name.upper()] = path

    pairs = []
    for name, vxl_path in vxl_files.items():
        if name in hva_files:
            pairs.append((vxl_path, hva_files[name]))

    return pairs


def main():
    print("=" * 60)
    print("VXL/HVA Section Name Fixer")
    print("=" * 60)

    if len(sys.argv) >= 3:
        # Fix specific pair
        vxl_path = sys.argv[1]
        hva_path = sys.argv[2]
        target_name = sys.argv[3] if len(sys.argv) > 3 else None

        if not os.path.exists(vxl_path):
            print(f"Error: VXL file not found: {vxl_path}")
            return

        if not os.path.exists(hva_path):
            print(f"Error: HVA file not found: {hva_path}")
            return

        fix_pair(vxl_path, hva_path, target_name)

    elif len(sys.argv) == 2:
        # Fix all pairs in specified directory
        directory = sys.argv[1]
        if not os.path.isdir(directory):
            print(f"Error: Directory not found: {directory}")
            return

        pairs = find_pairs(directory)
        if not pairs:
            print(f"No VXL/HVA pairs found in: {directory}")
            return

        print(f"\nFound {len(pairs)} pair(s):")
        for vxl, hva in pairs:
            print(f"  {os.path.basename(vxl)} + {os.path.basename(hva)}")

        for vxl, hva in pairs:
            fix_pair(vxl, hva)

    else:
        # Fix all pairs in current directory
        pairs = find_pairs('.')
        if not pairs:
            print("No VXL/HVA pairs found in current directory.")
            print("\nUsage:")
            print("  python fix_section_names.py                        # Fix all in current dir")
            print("  python fix_section_names.py <directory>            # Fix all in directory")
            print("  python fix_section_names.py file.vxl file.hva      # Fix specific pair")
            print("  python fix_section_names.py file.vxl file.hva body # Use specific name")
            return

        print(f"\nFound {len(pairs)} pair(s):")
        for vxl, hva in pairs:
            print(f"  {os.path.basename(vxl)} + {os.path.basename(hva)}")

        for vxl, hva in pairs:
            fix_pair(vxl, hva)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
