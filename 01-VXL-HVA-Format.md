# VXL and HVA File Format Reference

This document describes the binary file formats used by Red Alert 2/Yuri's Revenge for voxel models.

## VXL File Format (Voxel Model)

VXL files contain 3D voxel data for units and structures.

### Header Structure (34 bytes)

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 16 | char[16] | File type: "Voxel Animation" (null-padded) |
| 16 | 4 | uint32 | Unknown (usually 1) |
| 20 | 4 | uint32 | Number of limbs/sections |
| 24 | 4 | uint32 | Number of limbs (duplicate) |
| 28 | 4 | uint32 | Body data size in bytes |
| 32 | 2 | uint16 | Palette remap start index |

### Palette (768 bytes)

| Offset | Size | Description |
|--------|------|-------------|
| 34 | 768 | 256 colors x 3 bytes (RGB) |

**Note**: The palette is embedded but RA2/YR typically uses its own palette. The remap colors (indices 16-31) are used for team colors.

### Limb Headers (28 bytes each)

Starting at offset 802:

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 16 | char[16] | Section name (e.g., "body", "turret") |
| 16 | 4 | uint32 | Limb number |
| 20 | 4 | uint32 | Unknown 1 |
| 24 | 4 | uint32 | Unknown 2 |

**IMPORTANT**: The section name MUST match the corresponding HVA section name exactly!

### Body Data

Variable size, contains the actual voxel data for each limb.

### Limb Tailers (92 bytes each)

Located after body data. Contains bounding box and transform information.

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 4 | uint32 | Span start offset |
| 4 | 4 | uint32 | Span end offset |
| 8 | 4 | uint32 | Span data offset |
| 12 | 24 | float[6] | Transform matrix (partial) |
| 36 | 24 | float[6] | Bounding box min/max |
| 60 | 12 | bytes | Unknown |
| 72 | 4 | uint32 | Unknown |
| 76 | 4 | uint32 | Unknown |
| 80 | 1 | uint8 | **X dimension (width)** |
| 81 | 1 | uint8 | **Y dimension (length)** |
| 82 | 1 | uint8 | **Z dimension (height)** |
| 83 | 1 | uint8 | Normals mode |
| 84 | 8 | bytes | Padding/unknown |

**Critical**: If dimensions are 0x0x0, the VXL is broken and will not render!

### File Size Calculation

```
expected_size = 34 + 768 + (num_limbs * 28) + body_size + (num_limbs * 92)
```

---

## HVA File Format (Animation)

HVA files contain animation/transform data for VXL models.

### Header Structure (24 bytes)

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 16 | char[16] | Filename/identifier (can be zeros) |
| 16 | 4 | uint32 | Number of animation frames |
| 20 | 4 | uint32 | Number of sections |

### Section Names (16 bytes each)

Starting at offset 24:

| Offset | Size | Description |
|--------|------|-------------|
| 24 | 16 | Section 0 name |
| 40 | 16 | Section 1 name |
| ... | ... | ... |

**IMPORTANT**: Section names MUST match the VXL section names exactly!

### Transform Matrices

After section names, each frame has a 3x4 transform matrix per section.

| Per Section Per Frame | Size | Type |
|-----------------------|------|------|
| Transform Matrix | 48 bytes | float[12] |

Matrix layout (row-major):
```
[ ScaleX,  RotXY,   RotXZ,  TransX ]
[ RotYX,   ScaleY,  RotYZ,  TransY ]
[ RotZX,   RotZY,   ScaleZ, TransZ ]
```

### File Size Calculation

```
expected_size = 24 + (num_sections * 16) + (num_frames * num_sections * 48)
```

---

## Section Name Matching

The most common issue when exporting from Blender is section name mismatch:

### Common Mismatches

| VXL Section | HVA Section | Result |
|-------------|-------------|--------|
| "body" | "section0" | Model won't animate |
| "turret.001" | "turret" | Turret won't rotate |
| "model_LOD0" | "section0" | Model invisible |

### Valid Section Names

Standard RA2/YR section names:
- `body` - Main hull/chassis
- `turret` - Rotating turret
- `barrel` - Gun barrel
- `barone` - Barrel one (dual barrels)
- `bartwo` - Barrel two (dual barrels)

### Fixing Section Names

Use Python to fix section names:

```python
def fix_vxl_section_name(filepath, new_name):
    with open(filepath, 'rb') as f:
        data = bytearray(f.read())

    # Section name at offset 802 (after header + palette)
    new_bytes = new_name.encode('ascii')[:16].ljust(16, b'\x00')
    data[802:818] = new_bytes

    with open(filepath, 'wb') as f:
        f.write(data)

def fix_hva_section_name(filepath, new_name):
    with open(filepath, 'rb') as f:
        data = bytearray(f.read())

    # Section name at offset 24 (after header)
    new_bytes = new_name.encode('ascii')[:16].ljust(16, b'\x00')
    data[24:40] = new_bytes

    with open(filepath, 'wb') as f:
        f.write(data)
```

---

## Validation Checklist

When a VXL/HVA pair doesn't work, check:

1. **File type string**: Must be "Voxel Animation" (VXL only)
2. **Dimensions**: Must be non-zero (check tailer at offset 80-82)
3. **Section names**: VXL and HVA must match exactly
4. **File size**: Must match calculated expected size
5. **Limb count**: Must be > 0

---

## Python Validation Script

```python
import struct

def validate_vxl(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    # Check header
    file_type = data[0:16].rstrip(b'\x00')
    if file_type != b'Voxel Animation':
        print(f"ERROR: Invalid file type: {file_type}")
        return False

    # Get structure info
    num_limbs = struct.unpack_from('<I', data, 20)[0]
    body_size = struct.unpack_from('<I', data, 28)[0]

    # Get section name
    section_name = data[802:818].split(b'\x00')[0].decode('ascii')

    # Calculate tailer offset
    tailers_offset = 802 + (num_limbs * 28) + body_size

    # Read dimensions from tailer
    dim_x = data[tailers_offset + 80]
    dim_y = data[tailers_offset + 81]
    dim_z = data[tailers_offset + 82]

    print(f"Section: {section_name}")
    print(f"Dimensions: {dim_x} x {dim_y} x {dim_z}")

    if dim_x == 0 and dim_y == 0 and dim_z == 0:
        print("ERROR: Dimensions are 0x0x0 - VXL is broken!")
        return False

    return True
```

---

## References

- Westwood VXL format documentation
- XCC Utilities source code
- VXLSE (Voxel Section Editor) source
