# VXL and HVA File Format Reference

This document describes the binary file formats used by Red Alert 2/Yuri's Revenge for voxel models.

**Sources**: [tcrs/ra2ff VXLFile.cpp](https://github.com/tcrs/ra2ff/blob/master/src/VXLFile.cpp), [ModEnc VXL](https://modenc.renegadeprojects.com/VXL), [YR Argentina Tutorials](http://www.yrargentina.com/old/index.php?page=voxels/vxlg1)

---

## VXL File Format (Voxel Model)

VXL files contain 3D voxel data for units and structures.

### Header Structure (34 bytes)

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 16 | char[16] | File type: "Voxel Animation" (null-padded) |
| 16 | 4 | uint32 | Unknown (always 1) |
| 20 | 4 | uint32 | Number of limbs/sections |
| 24 | 4 | uint32 | Number of limbs (duplicate) |
| 28 | 4 | uint32 | Body data size in bytes |
| 32 | 1 | uint8 | **Palette remap START (should be 16)** |
| 33 | 1 | uint8 | **Palette remap END (should be 31)** |

**Critical**: Remap bytes at offset 32-33 must be set to 16-31 for team colors to work!

### Palette (768 bytes)

| Offset | Size | Description |
|--------|------|-------------|
| 34 | 768 | 256 colors x 3 bytes (RGB) |

**Note**: The palette is embedded but RA2/YR typically uses its own palette. Palette indices 16-31 are used for team colors.

### Limb Headers (28 bytes each)

Starting at offset 802:

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 16 | char[16] | Section name (e.g., "Body", "turret") |
| 16 | 4 | uint32 | Limb number (usually 0) |
| 20 | 4 | uint32 | Unknown 1 (usually 1) |
| 24 | 4 | uint32 | Unknown 2 (usually 0 or 2) |

**IMPORTANT**: The section name MUST match the corresponding HVA section name exactly!

### Body Data

Variable size, contains the voxel span data for each limb. Structure:

```
For each column (X * Y total):
  - Span start offset (uint32)
For each column:
  - Span end offset (uint32)
Span data:
  For each span in column:
    - skip (uint8) - Z position where voxels start
    - count (uint8) - number of voxels in span
    - [color, normal] × count - voxel data (2 bytes each)
    - count (uint8) - duplicate of count (required!)
  - End marker: skip (uint8), 0 (uint8)
```

Empty columns use 0xFFFFFFFF as both start and end offset.

### Limb Tailer (92 bytes) - CORRECTED FORMAT

Located after body data. This is the **correct** format based on source code analysis:

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0-3 | 4 | uint32 | Span start offset (in body) |
| 4-7 | 4 | uint32 | Span end offset (in body) |
| 8-11 | 4 | uint32 | Span data offset (in body) |
| 12-15 | 4 | float | **Scale** (single value, typically 0.083333) |
| 16-63 | 48 | float[12] | **Transform matrix** (3×4, 12 floats) |
| 64-75 | 12 | float[3] | **MinBounds** (x, y, z) |
| 76-87 | 12 | float[3] | **MaxBounds** (x, y, z) |
| 88 | 1 | uint8 | **X dimension (width)** |
| 89 | 1 | uint8 | **Y dimension (length)** |
| 90 | 1 | uint8 | **Z dimension (height)** |
| 91 | 1 | uint8 | **Normals mode** (2=TS, 4=RA2) |

**Critical**:
- Dimensions at offset 88-90 must be non-zero!
- Transform matrix should be identity: `[1,0,0,0, 0,1,0,0, 0,0,1,0]`
- MaxBounds should equal dimensions as floats

### File Layout

```
[Header 34 bytes]
[Palette 768 bytes]
[Limb Headers: 28 bytes × num_limbs]  <- starts at offset 802
[Body Data: variable]
[Limb Tailers: 92 bytes × num_limbs]
```

### File Size Calculation

```
expected_size = 34 + 768 + (num_limbs × 28) + body_size + (num_limbs × 92)
```

---

## HVA File Format (Animation)

HVA files contain animation/transform data for VXL models.

### Header Structure (24 bytes)

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 16 | char[16] | Filename/identifier (usually uppercase name) |
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

After section names, each frame has a 3×4 transform matrix per section.

| Per Section Per Frame | Size | Type |
|-----------------------|------|------|
| Transform Matrix | 48 bytes | float[12] |

Matrix layout (row-major):
```
[ ScaleX,  RotXY,   RotXZ,  TransX ]
[ RotYX,   ScaleY,  RotYZ,  TransY ]
[ RotZX,   RotZY,   ScaleZ, TransZ ]
```

For static models, use identity matrix:
```
[ 1.0, 0.0, 0.0, 0.0 ]
[ 0.0, 1.0, 0.0, 0.0 ]
[ 0.0, 0.0, 1.0, 0.0 ]
```

### File Size Calculation

```
expected_size = 24 + (num_sections × 16) + (num_frames × num_sections × 48)
```

---

## Span Data Format (Body Data)

The voxel data uses run-length encoding:

### Column Data Structure

For a VXL with dimensions X × Y × Z:
- Total columns: X × Y
- Column index: `col = y × X + x`

### Span Format

Each column contains spans of solid voxels:

```
[skip: uint8]     <- Z position where solid voxels start
[count: uint8]    <- number of solid voxels in this span
[color: uint8]    \
[normal: uint8]   / repeated 'count' times
[count: uint8]    <- duplicate of count (REQUIRED by game engine!)
... repeat for more spans ...
[skip: uint8]     <- remaining Z distance
[0: uint8]        <- 0 = end of column
```

### Empty Columns

Columns with no voxels use `0xFFFFFFFF` as both span start and end offset.

---

## Section Name Matching

The most common issue when exporting from Blender is section name mismatch:

### Standard Section Names

| Section | Purpose | File Suffix |
|---------|---------|-------------|
| `Body` | Main hull/chassis | (none) |
| `turret` | Rotating turret | TUR |
| `barrel` | Gun barrel | BARL |
| `barone` | Barrel one (dual) | BARONE |
| `bartwo` | Barrel two (dual) | BARTWO |

### Example File Names

For a unit called "MYTANK":
- Body: `MYTANK.vxl`, `MYTANK.hva` (section: "Body")
- Turret: `MYTANKTUR.vxl`, `MYTANKTUR.hva` (section: "turret")

### Fixing Section Names

```python
def fix_vxl_section_name(filepath, new_name):
    with open(filepath, 'rb') as f:
        data = bytearray(f.read())

    new_bytes = new_name.encode('ascii')[:16].ljust(16, b'\x00')
    data[802:818] = new_bytes

    with open(filepath, 'wb') as f:
        f.write(data)

def fix_hva_section_name(filepath, new_name):
    with open(filepath, 'rb') as f:
        data = bytearray(f.read())

    new_bytes = new_name.encode('ascii')[:16].ljust(16, b'\x00')
    data[24:40] = new_bytes

    with open(filepath, 'wb') as f:
        f.write(data)
```

---

## Validation Checklist

When a VXL/HVA pair doesn't work, check:

1. **File type string**: Must be "Voxel Animation" (VXL only)
2. **Remap bytes**: Offset 32-33 should be 16-31
3. **Dimensions**: Must be non-zero at tailer offset 88-90
4. **Section names**: VXL and HVA must match exactly
5. **Span data**: Must have proper skip/count/data/count format
6. **MaxBounds**: Should match dimensions as floats
7. **Normals mode**: Should be 4 for RA2/YR

---

## Python Validation Script

```python
import struct

def validate_vxl(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"File: {filepath}")
    print(f"Size: {len(data)} bytes")

    # Check header
    file_type = data[0:16].rstrip(b'\x00')
    if file_type != b'Voxel Animation':
        print(f"ERROR: Invalid file type: {file_type}")
        return False

    # Get structure info
    num_limbs = struct.unpack_from('<I', data, 20)[0]
    body_size = struct.unpack_from('<I', data, 28)[0]
    remap_start = data[32]
    remap_end = data[33]

    print(f"Limbs: {num_limbs}")
    print(f"Body size: {body_size}")
    print(f"Remap: {remap_start}-{remap_end}")

    if remap_start != 16 or remap_end != 31:
        print("WARNING: Remap should be 16-31 for team colors")

    # Get section name
    section_name = data[802:818].rstrip(b'\x00').decode('ascii')
    print(f"Section: {section_name}")

    # Calculate tailer offset
    tailer_off = 802 + (num_limbs * 28) + body_size

    # Read dimensions from tailer offset 88-90
    dim_x = data[tailer_off + 88]
    dim_y = data[tailer_off + 89]
    dim_z = data[tailer_off + 90]
    normals = data[tailer_off + 91]

    print(f"Dimensions: {dim_x} x {dim_y} x {dim_z}")
    print(f"Normals mode: {normals}")

    if dim_x == 0 or dim_y == 0 or dim_z == 0:
        print("ERROR: Dimensions contain zero - VXL is broken!")
        return False

    if normals != 4:
        print("WARNING: Normals mode should be 4 for RA2/YR")

    print("VXL structure appears valid")
    return True
```

---

## Resources

- [ModEnc VXL Documentation](https://modenc.renegadeprojects.com/VXL)
- [ModEnc HVA Documentation](https://modenc.renegadeprojects.com/HVA)
- [YR Argentina Voxel Tutorials](http://www.yrargentina.com/old/index.php?page=voxels/vxlg1)
- [ra2ff VXL Parser Source](https://github.com/tcrs/ra2ff/blob/master/src/VXLFile.cpp)
- [PPM Voxel Section Editor III](https://www.ppmsite.com/vxlseinfo/)
