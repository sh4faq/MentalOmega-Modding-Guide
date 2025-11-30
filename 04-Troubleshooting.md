# Troubleshooting Guide

Common issues and solutions when modding Mental Omega with custom VXL units.

---

## Issue: Model Not Visible (Invisible Unit)

### Symptoms
- Unit appears in build menu
- Unit can be built and selected
- Unit shadow may be visible
- Unit model is completely invisible

### Causes and Solutions

#### 1. VXL Dimensions are 0x0x0

**The most common cause!** The VXL file has invalid zero dimensions.

**Diagnosis:**
```python
import struct
with open('YOURUNIT.vxl', 'rb') as f:
    data = f.read()

# Read dimensions from tailer (offset 80-82 from tailer start)
num_limbs = struct.unpack_from('<I', data, 20)[0]
body_size = struct.unpack_from('<I', data, 28)[0]
tailer_offset = 802 + (num_limbs * 28) + body_size

dim_x = data[tailer_offset + 80]
dim_y = data[tailer_offset + 81]
dim_z = data[tailer_offset + 82]

print(f"Dimensions: {dim_x} x {dim_y} x {dim_z}")
```

If dimensions are 0x0x0, the VXL export failed.

**Solution:** Re-export from Blender with correct settings. Ensure:
- Model has actual geometry (not just an empty)
- Scale is applied before export
- Object is properly selected during export

#### 2. Section Name Mismatch

VXL and HVA section names don't match.

**Diagnosis:**
```python
# Check VXL section name (offset 802)
vxl_name = data[802:818].split(b'\x00')[0].decode('ascii')

# Check HVA section name (offset 24)
with open('YOURUNIT.hva', 'rb') as f:
    hva_data = f.read()
hva_name = hva_data[24:40].split(b'\x00')[0].decode('ascii')

print(f"VXL: '{vxl_name}', HVA: '{hva_name}'")
```

**Solution:** Use the fix_section_names.py script to make them match.

#### 3. Wrong Image Name in INI

The `Image=` property doesn't match the VXL filename.

**Solution:** Ensure exact match:
```ini
[YOURUNIT]
Image=YOURUNIT    ; Must match YOURUNIT.vxl exactly
```

#### 4. VXL/HVA Files Not Loading

The game can't find the VXL/HVA files.

**Solution - Use Loose Files (Recommended):**

Place VXL/HVA files directly in the Mental Omega folder as loose files. Loose files take priority over MIX archives!

```
Mental Omega/
├── TANKIE.vxl      ← Loose file loads first!
├── TANKIE.hva
├── TANKIETUR.vxl
└── TANKIETUR.hva
```

**Testing Approach:**
1. First test with `Image=HTNK` (vanilla Rhino Tank)
2. If that works, your INI is correct and the problem is your VXL files
3. Use a known working VXL (like IronFist `wrmn.vxl`) as a template

---

## Issue: Unit Not in Build Menu

### Symptoms
- Unit doesn't appear in any faction's build menu
- No error messages

### Causes and Solutions

#### 1. Not Registered in VehicleTypes

```ini
[VehicleTypes]
XX=YOURUNIT    ; XX = next available number
```

Check existing numbers in rules and use the next available.

#### 2. TechLevel is -1 or Missing

```ini
[YOURUNIT]
TechLevel=1    ; Must be >= 0
```

#### 3. Owner Not Set

```ini
[YOURUNIT]
Owner=Europeans,USSR    ; Must include factions you're testing with
```

#### 4. Prerequisite Building Missing

If you require a building that doesn't exist:
```ini
[YOURUNIT]
Prerequisite=    ; Empty = no prerequisites
```

---

## Issue: Turret Not Rotating

### Symptoms
- Tank body visible
- Turret either missing or doesn't rotate to face targets

### Causes and Solutions

#### 1. TurretAnim Not Set

```ini
[YOURUNIT]
Turret=yes
TurretAnim=YOURUNITTUR    ; Must match turret VXL name
```

#### 2. Turret VXL Missing

Ensure these files exist:
- `YOURUNITTUR.vxl`
- `YOURUNITTUR.hva`

And are included in the MIX file.

#### 3. Turret Section Name Mismatch

Turret VXL and HVA section names must match (usually "turret").

#### 4. ROT Value Missing

```ini
[YOURUNIT]
ROT=8    ; Rotation speed (lower = faster)
```

---

## Issue: Game Crashes on Load

### Symptoms
- Game crashes when loading
- Exception error or black screen

### Causes and Solutions

#### 1. Corrupted VXL File

The VXL file structure is invalid.

**Solution:** Validate the VXL:
```bash
python validate_vxl.py YOURUNIT.vxl
```

Look for:
- Invalid file type header
- Mismatched body size
- Invalid limb count

#### 2. MIX File Corruption

The MIX file has invalid structure.

**Solution:** Rebuild the MIX file from scratch.

#### 3. Duplicate Type Registration

Same unit registered twice in VehicleTypes.

**Solution:** Check for duplicate entries:
```ini
[VehicleTypes]
85=YOURUNIT
86=YOURUNIT    ; ERROR: Duplicate!
```

---

## Issue: Weapon Not Firing

### Symptoms
- Unit selects targets
- No weapon effects or damage

### Causes and Solutions

#### 1. Weapon Not Defined

```ini
[YOURUNIT]
Primary=YourWeapon    ; This weapon must exist

[YourWeapon]          ; Must be defined!
Damage=100
ROF=60
Range=7
...
```

#### 2. Range is Zero

```ini
[YourWeapon]
Range=7    ; Must be > 0
```

#### 3. Missing Warhead

```ini
[YourWeapon]
Warhead=YourWarhead    ; Must exist

[YourWarhead]
Verses=100%,100%,...   ; Must be defined
```

#### 4. Projectile Type Invalid

Use a known projectile type:
```ini
Projectile=Invisible      ; Instant hit
Projectile=InvisibleLow   ; Low instant hit
Projectile=AAHeatSeeker   ; Anti-air missile
```

---

## Issue: Wrong Team Colors

### Symptoms
- Unit uses wrong colors
- Unit has no team colors

### Causes and Solutions

#### 1. Remapable Not Set

```ini
[YOURUNIT]
Remapable=yes
```

#### 2. VXL Palette Issues

The VXL must use palette indices 16-31 for team color areas.

**Solution:** In Blender, use remap colors when texturing.

---

## Issue: Unit Falls Through Ground

### Symptoms
- Unit spawns below terrain
- Unit sinks into ground

### Causes and Solutions

#### 1. Wrong Locomotor

Ensure correct locomotor for vehicle type:
```ini
Locomotor={4A582741-9839-11d1-B709-00A024DDAFD1}    ; Tracked vehicle
```

#### 2. SpeedType Mismatch

```ini
SpeedType=Track    ; For tracked vehicles
SpeedType=Wheel    ; For wheeled vehicles
SpeedType=Hover    ; For hovercraft
```

---

## Diagnostic Python Scripts

### Quick VXL Check

```python
import struct
import sys

def quick_check(vxl_path):
    with open(vxl_path, 'rb') as f:
        data = f.read()

    print(f"File: {vxl_path}")
    print(f"Size: {len(data)} bytes")

    # Header
    file_type = data[0:16].rstrip(b'\x00')
    print(f"Type: {file_type}")

    if file_type != b'Voxel Animation':
        print("ERROR: Invalid file type!")
        return

    # Structure
    num_limbs = struct.unpack_from('<I', data, 20)[0]
    body_size = struct.unpack_from('<I', data, 28)[0]
    section = data[802:818].split(b'\x00')[0].decode('ascii')

    print(f"Limbs: {num_limbs}")
    print(f"Body size: {body_size}")
    print(f"Section: '{section}'")

    # Dimensions
    tailer_off = 802 + (num_limbs * 28) + body_size
    dims = (data[tailer_off+80], data[tailer_off+81], data[tailer_off+82])
    print(f"Dimensions: {dims[0]} x {dims[1]} x {dims[2]}")

    if dims == (0, 0, 0):
        print("\n*** ERROR: Zero dimensions - VXL is broken! ***")
    else:
        print("\n*** VXL structure looks OK ***")

if __name__ == "__main__":
    quick_check(sys.argv[1] if len(sys.argv) > 1 else "FTNKNEXUS.vxl")
```

### Batch Validation

```python
import os
import glob

def validate_all(directory):
    vxl_files = glob.glob(os.path.join(directory, "*.vxl"))
    hva_files = glob.glob(os.path.join(directory, "*.hva"))

    print(f"Found {len(vxl_files)} VXL files, {len(hva_files)} HVA files\n")

    for vxl in vxl_files:
        base = os.path.splitext(vxl)[0]
        hva = base + ".hva"

        if os.path.exists(hva):
            print(f"Pair: {os.path.basename(vxl)} + {os.path.basename(hva)}")
            # Add validation here
        else:
            print(f"WARNING: No HVA for {os.path.basename(vxl)}")
```

---

## Getting Help

If issues persist:

1. **Check game logs**: Look in Mental Omega folder for debug/error logs
2. **Use syringe.log**: If available, shows mod loading issues
3. **Test with vanilla unit**: Replace Image= with a known working unit (e.g., HTNK) to isolate VXL issues
4. **Community resources**: PPM (Project Perfect Mod) forums have extensive RA2 modding support
