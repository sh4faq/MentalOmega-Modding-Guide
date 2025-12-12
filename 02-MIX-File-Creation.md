# MIX File Creation Guide

MIX files are Westwood's archive format used by Command & Conquer games. This guide explains how to create MIX files for Mental Omega modding.

## MIX File Format Overview

MIX files are simple archives that bundle multiple files together. RA2/YR uses unencrypted MIX files with a simple structure.

### File Structure

```
+------------------+
| Header (10 bytes)|
+------------------+
| Index Entries    |
| (12 bytes each)  |
+------------------+
| File Bodies      |
| (raw data)       |
+------------------+
```

### Header Structure (10 bytes)

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 4 | uint32 | Flags (0 = unencrypted) |
| 4 | 2 | uint16 | Number of files |
| 6 | 4 | uint32 | Total body size |

### Index Entry Structure (12 bytes each)

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 4 | uint32 | File ID (CRC hash of filename) |
| 4 | 4 | uint32 | Offset in body section |
| 8 | 4 | uint32 | File size |

**Important**: Index entries must be sorted by File ID in ascending order!

---

## File ID Calculation

RA2/YR uses a CRC-like hash to generate file IDs from filenames:

```python
def calculate_file_id(filename):
    """Calculate Westwood-style file ID from filename"""
    name = filename.upper()
    id = 0
    for char in name:
        id = ((id << 1) | (id >> 31)) + ord(char)
        id &= 0xFFFFFFFF  # Keep as 32-bit
    return id
```

### Example IDs

| Filename | File ID |
|----------|---------|
| FTNKNEXUS.vxl | 0x00096814 |
| FTNKNEXUS.hva | 0x000967CD |
| FTNKNEXUSTUR.vxl | 0x004B4B04 |
| FTNKNEXUSTUR.hva | 0x004B4ABD |

---

## Mental Omega MIX File Naming

Mental Omega looks for expansion MIX files with specific naming:

| Pattern | Range | Priority |
|---------|-------|----------|
| expandmo00.mix - expandmo99.mix | 00-99 | Higher number = higher priority |

**Recommendation**: Use `expandmo02.mix` or higher to avoid conflicts with base game files.

---

## Complete Python MIX Creator

```python
"""
MIX File Creator for Mental Omega / RA2 / YR
Creates unencrypted MIX archives compatible with the game engine.
"""
import struct
import os

def calculate_file_id(filename):
    """Generate Westwood-style ID from filename"""
    name = filename.upper()
    id = 0
    for char in name:
        id = ((id << 1) | (id >> 31)) + ord(char)
        id &= 0xFFFFFFFF
    return id

def create_mix(output_path, files):
    """
    Create a MIX file from a list of file paths.

    Args:
        output_path: Path for the output MIX file
        files: List of file paths to include
    """
    # Read all files and calculate IDs
    file_data = []
    for filepath in files:
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            data = f.read()
        file_id = calculate_file_id(filename)
        file_data.append((file_id, filename, data))

    # Sort by ID (REQUIRED by MIX format)
    file_data.sort(key=lambda x: x[0])

    # Calculate offsets
    num_files = len(file_data)
    current_offset = 0
    index_entries = []
    body_size = 0

    for file_id, filename, data in file_data:
        size = len(data)
        index_entries.append((file_id, current_offset, size))
        current_offset += size
        body_size += size

    # Write MIX file
    with open(output_path, 'wb') as f:
        # Header
        f.write(struct.pack('<I', 0))        # Flags (0 = no encryption)
        f.write(struct.pack('<H', num_files)) # Number of files
        f.write(struct.pack('<I', body_size)) # Body size

        # Index entries
        for file_id, offset, size in index_entries:
            f.write(struct.pack('<I', file_id))
            f.write(struct.pack('<I', offset))
            f.write(struct.pack('<I', size))

        # File bodies
        for file_id, filename, data in file_data:
            f.write(data)

    print(f"Created: {output_path}")
    print(f"Files: {num_files}")
    for file_id, filename, data in file_data:
        print(f"  {filename} (ID: 0x{file_id:08X}, {len(data)} bytes)")

# Usage example
if __name__ == "__main__":
    files = [
        "FTNKNEXUS.vxl",
        "FTNKNEXUS.hva",
        "FTNKNEXUSTUR.vxl",
        "FTNKNEXUSTUR.hva"
    ]

    create_mix("expandmo02.mix", files)
```

---

## Step-by-Step Usage

### 1. Prepare Your Files

Gather all files you want to include:
- VXL files (voxel models)
- HVA files (animations)
- SHP files (sprites) if any
- Any other game assets

### 2. Run the Script

```bash
python create_mix.py
```

### 3. Copy to Game Directory

Copy the generated MIX file to your Mental Omega installation folder.

### 4. Verify with XCC Mixer (Optional)

Use XCC Mixer to open and verify your MIX file contains all expected files.

---

## File Types You Can Include

| Extension | Type | Description |
|-----------|------|-------------|
| .vxl | Voxel | 3D voxel models |
| .hva | Animation | Voxel animation data |
| .shp | Sprite | 2D sprite images |
| .pal | Palette | Color palette |
| .ini | Config | (Usually not in MIX for MO) |
| .wav | Audio | Sound effects |
| .aud | Audio | Compressed audio |
| .csf | Strings | String table |

---

## Troubleshooting

### "File not found in game"

1. Check filename is uppercase in the MIX
2. Verify file ID was calculated correctly
3. Ensure MIX is in the correct location
4. Check MIX filename follows expandmoXX.mix pattern

### "MIX file won't load"

1. Verify header flags are 0 (not encrypted)
2. Check index entries are sorted by ID
3. Verify body size matches sum of all file sizes
4. Check file offsets are calculated correctly

### "Assets load but don't render"

1. This is likely a VXL/HVA issue, not MIX issue
2. See VXL/HVA troubleshooting guide

---

## Advanced: Reading MIX Files

```python
def read_mix(filepath):
    """Read and list contents of a MIX file"""
    with open(filepath, 'rb') as f:
        # Read header
        flags = struct.unpack('<I', f.read(4))[0]
        num_files = struct.unpack('<H', f.read(2))[0]
        body_size = struct.unpack('<I', f.read(4))[0]

        print(f"Flags: {flags}")
        print(f"Files: {num_files}")
        print(f"Body size: {body_size}")

        # Read index
        for i in range(num_files):
            file_id = struct.unpack('<I', f.read(4))[0]
            offset = struct.unpack('<I', f.read(4))[0]
            size = struct.unpack('<I', f.read(4))[0]
            print(f"  ID: 0x{file_id:08X}, Offset: {offset}, Size: {size}")
```

---

## References

- XCC Utilities source code
- RA2 Modding documentation
- Mental Omega modding resources
