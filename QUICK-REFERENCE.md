# Quick Reference Card

## File Naming Convention

| Type | Body | Turret | Barrel |
|------|------|--------|--------|
| VXL | `UNITNAME.vxl` | `UNITNAMETUR.vxl` | `UNITNAMEBARL.vxl` |
| HVA | `UNITNAME.hva` | `UNITNAMETUR.hva` | `UNITNAMEBARL.hva` |

## Section Names

| Part | VXL Section | HVA Section |
|------|-------------|-------------|
| Body | `body` | `body` |
| Turret | `turret` | `turret` |
| Barrel | `barrel` | `barrel` |

**Rule: VXL and HVA section names MUST match!**

## Key File Offsets

| File | Offset | Data |
|------|--------|------|
| VXL | 0-16 | "Voxel Animation" |
| VXL | 20 | Number of limbs (uint32) |
| VXL | 28 | Body size (uint32) |
| VXL | 802 | Section name (16 bytes) |
| VXL | tailer+80 | Dimensions X,Y,Z (3 bytes) |
| HVA | 16 | Number of frames (uint32) |
| HVA | 20 | Number of sections (uint32) |
| HVA | 24 | Section name (16 bytes) |

## VXL Tailer Offset Calculation

```
tailer_offset = 802 + (num_limbs * 28) + body_size
```

## Common Commands

### Validate VXL
```bash
python validate_vxl.py UNITNAME.vxl
```

### Fix Section Names
```bash
python fix_section_names.py UNITNAME.vxl UNITNAME.hva body
```

### Create MIX
```bash
python create_mix.py expandmo02.mix *.vxl *.hva
```

### Full Preparation
```bash
python prepare_tank.py UNITNAME source_folder output_folder
```

## Minimum INI for Tank

```ini
[VehicleTypes]
XX=UNITNAME

[UNITNAME]
Image=UNITNAME
Name=Unit Name
Primary=WeaponName
TechLevel=1
Cost=1000
Speed=6
Owner=Europeans
Strength=500
Armor=heavy
Turret=yes
TurretAnim=UNITNAMETUR
SpeedType=Track
Locomotor={4A582741-9839-11d1-B709-00A024DDAFD1}
Voxel=yes
```

## Common Locomotors

| GUID | Type |
|------|------|
| `{4A582741-9839-11d1-B709-00A024DDAFD1}` | Tracked/Wheeled |
| `{4A582742-9839-11d1-B709-00A024DDAFD1}` | Hover |
| `{4A582744-9839-11d1-B709-00A024DDAFD1}` | Mech/Walk |
| `{4A582746-9839-11d1-B709-00A024DDAFD1}` | Fly |
| `{4A582747-9839-11d1-B709-00A024DDAFD1}` | Ship |

## Troubleshooting Checklist

- [ ] VXL dimensions non-zero?
- [ ] Section names match?
- [ ] Files in MIX?
- [ ] Image= matches filename?
- [ ] Voxel=yes set?
- [ ] TechLevel >= 0?
- [ ] Owner includes test faction?

## MIX File Structure

```
[4 bytes]  Flags (0)
[2 bytes]  File count
[4 bytes]  Body size
[N x 12]   Index entries (ID, offset, size)
[...]      File bodies
```

## Mental Omega Paths

| File | Purpose |
|------|---------|
| `expandmo02.mix` | Custom assets |
| `INI/Map Code/Standard.ini` | Custom rules |

## Python Quick Snippets

### Read VXL Dimensions
```python
import struct
with open('file.vxl', 'rb') as f:
    data = f.read()
num_limbs = struct.unpack_from('<I', data, 20)[0]
body_size = struct.unpack_from('<I', data, 28)[0]
t = 802 + (num_limbs * 28) + body_size
print(data[t+80], data[t+81], data[t+82])
```

### Check Section Names
```python
# VXL section at offset 802
vxl_section = open('f.vxl','rb').read()[802:818].split(b'\x00')[0]
# HVA section at offset 24
hva_section = open('f.hva','rb').read()[24:40].split(b'\x00')[0]
print(vxl_section, hva_section)
```
