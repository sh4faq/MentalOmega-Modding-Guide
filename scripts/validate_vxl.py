"""
VXL File Validator for Red Alert 2 / Mental Omega
Checks VXL file structure and reports issues.

Usage:
    python validate_vxl.py [filename.vxl]
    python validate_vxl.py  (validates all .vxl in current directory)
"""
import struct
import os
import sys
import glob


def validate_vxl(filepath):
    """Validate a VXL file and return issues, warnings, info."""
    issues = []
    warnings = []
    info = []

    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return ["File not found"], [], []
    except Exception as e:
        return [f"Error reading file: {e}"], [], []

    file_size = len(data)
    info.append(f"File size: {file_size} bytes")

    # Size check
    if file_size > 100000:
        warnings.append(f"File is unusually large ({file_size} bytes). Typical tanks are 10-50KB.")

    # Header validation
    if len(data) < 34:
        issues.append("File too small - incomplete header")
        return issues, warnings, info

    # File type string
    file_type = data[0:16].rstrip(b'\x00')
    if file_type != b'Voxel Animation':
        issues.append(f"Invalid file type: '{file_type.decode('ascii', errors='replace')}' (expected 'Voxel Animation')")
    else:
        info.append("File type: Valid 'Voxel Animation' header")

    # Header values
    unknown1 = struct.unpack_from('<I', data, 16)[0]
    num_limbs = struct.unpack_from('<I', data, 20)[0]
    num_limbs2 = struct.unpack_from('<I', data, 24)[0]
    body_size = struct.unpack_from('<I', data, 28)[0]
    palette_remap = struct.unpack_from('<H', data, 32)[0]

    info.append(f"Number of limbs: {num_limbs}")
    info.append(f"Body size: {body_size} bytes")

    if num_limbs == 0:
        issues.append("Number of limbs is 0 - invalid VXL")
    elif num_limbs > 10:
        warnings.append(f"Unusual number of limbs ({num_limbs}). Most tanks have 1-3.")

    if num_limbs != num_limbs2:
        warnings.append(f"Limb count mismatch: {num_limbs} vs {num_limbs2}")

    # Palette check
    palette_offset = 34
    palette_end = palette_offset + 768

    if len(data) < palette_end:
        issues.append("File too small for palette data")
        return issues, warnings, info

    palette = data[palette_offset:palette_end]
    if palette == b'\x00' * 768:
        warnings.append("Palette is all zeros - may be invalid")

    # Limb headers
    limb_headers_offset = 802

    for i in range(num_limbs):
        limb_offset = limb_headers_offset + (i * 28)

        if limb_offset + 28 > len(data):
            issues.append(f"File too small for limb {i} header")
            break

        section_name = data[limb_offset:limb_offset+16].rstrip(b'\x00')
        section_name_str = section_name.decode('ascii', errors='replace')
        info.append(f"Limb {i} section name: '{section_name_str}'")

        if len(section_name) == 0:
            issues.append(f"Limb {i} has empty section name")

    # Calculate tailer offset and check dimensions
    limb_headers_size = num_limbs * 28
    body_start = limb_headers_offset + limb_headers_size
    tailers_offset = body_start + body_size

    info.append(f"Body data starts at: {body_start}")
    info.append(f"Tailers start at: {tailers_offset}")

    expected_file_size = tailers_offset + (num_limbs * 92)
    info.append(f"Expected file size: {expected_file_size}")

    if file_size != expected_file_size:
        diff = file_size - expected_file_size
        warnings.append(f"File size mismatch: actual={file_size}, expected={expected_file_size} (diff={diff})")

    # Check dimensions in tailer
    if tailers_offset + 92 <= len(data):
        dim_x = data[tailers_offset + 80]
        dim_y = data[tailers_offset + 81]
        dim_z = data[tailers_offset + 82]

        info.append(f"Dimensions: {dim_x} x {dim_y} x {dim_z}")

        if dim_x == 0 and dim_y == 0 and dim_z == 0:
            issues.append("CRITICAL: Dimensions are 0x0x0 - VXL is broken/empty!")
    else:
        warnings.append("Could not read tailer - file may be truncated")

    return issues, warnings, info


def validate_hva(filepath):
    """Validate an HVA file."""
    issues = []
    warnings = []
    info = []

    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return ["File not found"], [], []
    except Exception as e:
        return [f"Error reading file: {e}"], [], []

    file_size = len(data)
    info.append(f"File size: {file_size} bytes")

    if file_size < 24:
        issues.append("File too small for HVA header")
        return issues, warnings, info

    filename = data[0:16].rstrip(b'\x00')
    num_frames = struct.unpack_from('<I', data, 16)[0]
    num_sections = struct.unpack_from('<I', data, 20)[0]

    info.append(f"Filename field: '{filename.decode('ascii', errors='replace')}'")
    info.append(f"Number of frames: {num_frames}")
    info.append(f"Number of sections: {num_sections}")

    if num_frames == 0:
        issues.append("Number of frames is 0")

    if num_sections == 0:
        issues.append("Number of sections is 0")

    # Section names
    section_names_offset = 24
    for i in range(num_sections):
        name_offset = section_names_offset + (i * 16)
        if name_offset + 16 > len(data):
            issues.append(f"File too small for section {i} name")
            break

        section_name = data[name_offset:name_offset+16].rstrip(b'\x00')
        info.append(f"Section {i}: '{section_name.decode('ascii', errors='replace')}'")

    # File size check
    matrices_offset = section_names_offset + (num_sections * 16)
    expected_matrices_size = num_frames * num_sections * 48
    expected_file_size = matrices_offset + expected_matrices_size

    if file_size != expected_file_size:
        diff = file_size - expected_file_size
        warnings.append(f"File size mismatch: actual={file_size}, expected={expected_file_size} (diff={diff})")

    return issues, warnings, info


def print_results(filepath, issues, warnings, info):
    """Print validation results."""
    print("=" * 60)
    print(f"FILE: {filepath}")
    print("=" * 60)

    print("\n--- INFO ---")
    for item in info:
        print(f"  {item}")

    print("\n--- WARNINGS ---")
    if warnings:
        for item in warnings:
            print(f"  [!] {item}")
    else:
        print("  None")

    print("\n--- ISSUES ---")
    if issues:
        for item in issues:
            print(f"  [X] {item}")
    else:
        print("  None - Structure looks valid")

    print()


def main():
    if len(sys.argv) > 1:
        # Validate specific file(s)
        files = sys.argv[1:]
    else:
        # Validate all VXL/HVA in current directory
        files = glob.glob("*.vxl") + glob.glob("*.hva")

    if not files:
        print("No VXL/HVA files found.")
        print("Usage: python validate_vxl.py [file1.vxl] [file2.hva] ...")
        return

    for filepath in files:
        ext = os.path.splitext(filepath)[1].lower()

        if ext == '.vxl':
            issues, warnings, info = validate_vxl(filepath)
        elif ext == '.hva':
            issues, warnings, info = validate_hva(filepath)
        else:
            print(f"Skipping unknown file type: {filepath}")
            continue

        print_results(filepath, issues, warnings, info)


if __name__ == "__main__":
    main()
