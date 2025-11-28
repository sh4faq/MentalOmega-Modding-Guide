"""
Complete Tank Preparation Script
Processes exported Blender files and prepares them for Mental Omega.

This script:
1. Validates VXL/HVA files
2. Fixes section names
3. Renames to proper RA2 naming convention
4. Creates MIX file

Usage:
    python prepare_tank.py UNITNAME [source_directory] [output_directory]

Example:
    python prepare_tank.py FTNKNEXUS C:\exports C:\MentalOmega

Expects these files in source directory:
    - tankbody.vxl
    - tankbody.hva
    - tankturret.vxl (optional, for tanks with turrets)
    - tankturret.hva (optional)
"""
import struct
import os
import sys
import shutil


def validate_vxl(filepath):
    """Quick VXL validation - returns (valid, dimensions, section_name)"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()

        # Check header
        file_type = data[0:16].rstrip(b'\x00')
        if file_type != b'Voxel Animation':
            return False, (0, 0, 0), ""

        # Get structure info
        num_limbs = struct.unpack_from('<I', data, 20)[0]
        body_size = struct.unpack_from('<I', data, 28)[0]

        # Get section name
        section_name = data[802:818].split(b'\x00')[0].decode('ascii', errors='replace')

        # Get dimensions
        tailers_offset = 802 + (num_limbs * 28) + body_size
        dim_x = data[tailers_offset + 80]
        dim_y = data[tailers_offset + 81]
        dim_z = data[tailers_offset + 82]

        valid = not (dim_x == 0 and dim_y == 0 and dim_z == 0)
        return valid, (dim_x, dim_y, dim_z), section_name

    except Exception as e:
        return False, (0, 0, 0), str(e)


def get_hva_section_name(filepath):
    """Get section name from HVA file."""
    with open(filepath, 'rb') as f:
        f.seek(24)
        return f.read(16).split(b'\x00')[0].decode('ascii', errors='replace')


def fix_section_name(filepath, new_name, is_vxl=True):
    """Fix section name in VXL or HVA file."""
    with open(filepath, 'rb') as f:
        data = bytearray(f.read())

    offset = 802 if is_vxl else 24
    new_bytes = new_name.encode('ascii')[:16].ljust(16, b'\x00')
    data[offset:offset+16] = new_bytes

    with open(filepath, 'wb') as f:
        f.write(data)


def calculate_file_id(filename):
    """Calculate MIX file ID."""
    name = filename.upper()
    file_id = 0
    for char in name:
        file_id = ((file_id << 1) | (file_id >> 31)) + ord(char)
        file_id &= 0xFFFFFFFF
    return file_id


def create_mix(output_path, files):
    """Create MIX file."""
    file_data = []
    for filepath in files:
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            data = f.read()
        file_id = calculate_file_id(filename)
        file_data.append((file_id, filename, data))

    file_data.sort(key=lambda x: x[0])

    num_files = len(file_data)
    current_offset = 0
    index_entries = []
    body_size = 0

    for file_id, filename, data in file_data:
        size = len(data)
        index_entries.append((file_id, current_offset, size))
        current_offset += size
        body_size += size

    with open(output_path, 'wb') as f:
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<H', num_files))
        f.write(struct.pack('<I', body_size))

        for file_id, offset, size in index_entries:
            f.write(struct.pack('<I', file_id))
            f.write(struct.pack('<I', offset))
            f.write(struct.pack('<I', size))

        for file_id, filename, data in file_data:
            f.write(data)

    return num_files


def main():
    print("=" * 60)
    print("Tank Preparation Script for Mental Omega")
    print("=" * 60)

    # Parse arguments
    if len(sys.argv) < 2:
        print("\nUsage: python prepare_tank.py UNITNAME [source_dir] [output_dir]")
        print("\nExample:")
        print("  python prepare_tank.py FTNKNEXUS")
        print("  python prepare_tank.py FTNKNEXUS C:\\exports C:\\MentalOmega")
        return

    unit_name = sys.argv[1].upper()
    source_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    output_dir = sys.argv[3] if len(sys.argv) > 3 else '.'

    print(f"\nUnit name: {unit_name}")
    print(f"Source directory: {source_dir}")
    print(f"Output directory: {output_dir}")

    # Check for source files
    body_vxl = os.path.join(source_dir, 'tankbody.vxl')
    body_hva = os.path.join(source_dir, 'tankbody.hva')
    turret_vxl = os.path.join(source_dir, 'tankturret.vxl')
    turret_hva = os.path.join(source_dir, 'tankturret.hva')

    has_body = os.path.exists(body_vxl) and os.path.exists(body_hva)
    has_turret = os.path.exists(turret_vxl) and os.path.exists(turret_hva)

    if not has_body:
        print("\nError: tankbody.vxl and tankbody.hva not found in source directory!")
        return

    print(f"\nFound body files: {has_body}")
    print(f"Found turret files: {has_turret}")

    # Validate body
    print("\n--- Validating Body ---")
    valid, dims, section = validate_vxl(body_vxl)
    print(f"  VXL valid: {valid}")
    print(f"  Dimensions: {dims[0]} x {dims[1]} x {dims[2]}")
    print(f"  Section name: '{section}'")

    if not valid:
        print("\n  ERROR: Body VXL has invalid dimensions!")
        print("  Re-export from Blender with proper settings.")
        return

    hva_section = get_hva_section_name(body_hva)
    print(f"  HVA section: '{hva_section}'")

    if section != hva_section:
        print("  Section name mismatch detected!")

    # Validate turret if present
    if has_turret:
        print("\n--- Validating Turret ---")
        valid, dims, section = validate_vxl(turret_vxl)
        print(f"  VXL valid: {valid}")
        print(f"  Dimensions: {dims[0]} x {dims[1]} x {dims[2]}")
        print(f"  Section name: '{section}'")

        if not valid:
            print("\n  ERROR: Turret VXL has invalid dimensions!")
            return

        hva_section = get_hva_section_name(turret_hva)
        print(f"  HVA section: '{hva_section}'")

    # Prepare output files
    print("\n--- Preparing Output Files ---")

    target_body_vxl = os.path.join(output_dir, f'{unit_name}.vxl')
    target_body_hva = os.path.join(output_dir, f'{unit_name}.hva')

    # Copy body files
    shutil.copy(body_vxl, target_body_vxl)
    shutil.copy(body_hva, target_body_hva)
    print(f"  Copied body -> {unit_name}.vxl, {unit_name}.hva")

    # Fix body section names to 'body'
    fix_section_name(target_body_vxl, 'body', is_vxl=True)
    fix_section_name(target_body_hva, 'body', is_vxl=False)
    print("  Fixed body section names to 'body'")

    output_files = [target_body_vxl, target_body_hva]

    # Handle turret if present
    if has_turret:
        target_turret_vxl = os.path.join(output_dir, f'{unit_name}TUR.vxl')
        target_turret_hva = os.path.join(output_dir, f'{unit_name}TUR.hva')

        shutil.copy(turret_vxl, target_turret_vxl)
        shutil.copy(turret_hva, target_turret_hva)
        print(f"  Copied turret -> {unit_name}TUR.vxl, {unit_name}TUR.hva")

        fix_section_name(target_turret_vxl, 'turret', is_vxl=True)
        fix_section_name(target_turret_hva, 'turret', is_vxl=False)
        print("  Fixed turret section names to 'turret'")

        output_files.extend([target_turret_vxl, target_turret_hva])

    # Create MIX file
    print("\n--- Creating MIX File ---")
    mix_path = os.path.join(output_dir, 'expandmo02.mix')
    num_files = create_mix(mix_path, output_files)
    print(f"  Created {mix_path} with {num_files} files")

    # Generate INI snippet
    print("\n--- INI Configuration ---")
    print("Add this to INI/Map Code/Standard.ini:")
    print("-" * 40)
    print(f"""
[VehicleTypes]
XX={unit_name}

[{unit_name}]
Image={unit_name}
UIName=Name:{unit_name}
Name=Your Unit Name
Category=AFV
Primary=YourWeapon
TechLevel=1
Cost=1000
Speed=6
Sight=7
Owner=Europeans,USSR
Strength=500
Armor=heavy
ROT=8
Turret={'yes' if has_turret else 'no'}
{'TurretAnim=' + unit_name + 'TUR' if has_turret else ''}
Crusher=yes
MovementZone=Normal
SpeedType=Track
Locomotor={{4A582741-9839-11d1-B709-00A024DDAFD1}}
Voxel=yes
Remapable=yes
Cameo=YOURUNITCAMEO
""")
    print("-" * 40)

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"\nFiles created in: {output_dir}")
    for f in output_files:
        print(f"  {os.path.basename(f)}")
    print(f"  expandmo02.mix")
    print("\nNext steps:")
    print("1. Copy expandmo02.mix to your Mental Omega folder")
    print("2. Add the INI configuration above to Standard.ini")
    print("3. Launch the game and test!")


if __name__ == "__main__":
    main()
