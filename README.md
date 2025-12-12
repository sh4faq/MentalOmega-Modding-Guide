# Red Alert 2 Mental Omega 3.3.6 Custom Unit Modding Guide

A comprehensive guide for adding custom voxel units to Mental Omega 3.3.6 (Red Alert 2: Yuri's Revenge mod).

## Table of Contents

1. [Overview](#overview)
2. [Quick Start - Working Example](#quick-start---working-example)
3. [Project Structure](#project-structure)
4. [Documentation Files](#documentation-files)
5. [Tools Required](#tools-required)
6. [Mental Omega Unit IDs](#mental-omega-unit-ids)
7. [Faction Names](#faction-names)

## Overview

This guide documents the process of adding custom voxel units to Mental Omega 3.3.6.

### Key Discoveries

1. **Loose Files Over MIX**: Place VXL/HVA files directly in the Mental Omega folder - they load before MIX archives
2. **Use Standard.ini**: Modify units via `INI/Map Code/Standard.ini` - it's loaded for Standard game mode
3. **Image= Override**: Use `Image=NEWMODEL` to replace a unit's visual model
4. **Section Names Must Match**: VXL and HVA section names must be identical
5. **Working Reference**: IronFist example (`wrmn.vxl`/`wrmn.hva`) is a known working VXL/HVA pair
6. **VOX Export Workflow**: Export Blender models to VOX format first for maximum quality (256³ resolution), then convert to VXL

## Quick Start - Working Example

This example replaces the Bulldog Tank (ETNK) with a custom model, available for all factions.

### Step 1: Get Working VXL Files

Use the IronFist example files as a template:
```
C:\Users\hamze\Desktop\IronFist Example\wrmn.vxl  (44101 bytes)
C:\Users\hamze\Desktop\IronFist Example\wrmn.hva  (88 bytes)
```

### Step 2: Copy Files to Game Folder

Copy and rename the files to your Mental Omega directory:
```
wrmn.vxl  ->  C:\...\Mental Omega\TANKIE.vxl
wrmn.hva  ->  C:\...\Mental Omega\TANKIE.hva
wrmn.vxl  ->  C:\...\Mental Omega\TANKIETUR.vxl  (for turret)
wrmn.hva  ->  C:\...\Mental Omega\TANKIETUR.hva  (for turret)
```

### Step 3: Configure INI

Edit `Mental Omega\INI\Map Code\Standard.ini`:

```ini
[ETNK]
; Replace Bulldog Tank with custom model
Image=TANKIE
Strength=9999
Cost=1
Speed=10
Turret=yes
ROT=8
Owner=British,French,Germans,Americans,Alliance,Russians,Confederation,Africans,Arabs,YuriCountry
Prerequisite=
Primary=TankieGun

; Custom weapon with 5000 damage
[TankieGun]
Damage=5000
ROF=50
Range=6
Projectile=InvisibleLow
Speed=100
Warhead=SA
Bright=yes
```

### Step 4: Test

1. Launch Mental Omega
2. Start a **Standard** mode skirmish
3. Play as **any faction**
4. Build the Bulldog Tank from your War Factory
5. It should appear with the IronFist model, cost $1, have 9999 HP

## Project Structure

```
Mental Omega/
├── TANKIE.vxl              # Tank body voxel (loose file - loads first!)
├── TANKIE.hva              # Tank body animation
├── TANKIETUR.vxl           # Tank turret voxel
├── TANKIETUR.hva           # Tank turret animation
└── INI/
    └── Map Code/
        └── Standard.ini    # Custom unit definitions (Standard mode)
```

**Important**: Loose VXL/HVA files in the game folder take priority over MIX archives!

## Documentation Files

| File | Description |
|------|-------------|
| [01-VXL-HVA-Format.md](01-VXL-HVA-Format.md) | VXL/HVA file format specification |
| [02-MIX-File-Creation.md](02-MIX-File-Creation.md) | How to create MIX archive files |
| [03-INI-Configuration.md](03-INI-Configuration.md) | Unit INI configuration reference |
| [04-Troubleshooting.md](04-Troubleshooting.md) | Common issues and solutions |
| [05-Blender-Export.md](05-Blender-Export.md) | Blender VXL export settings |
| [06-Tools-Reference.md](06-Tools-Reference.md) | Complete modding tools reference |
| [QUICK-REFERENCE.md](QUICK-REFERENCE.md) | Quick reference cheat sheet |

## Tools Required

### Essential
- **Python 3.x** - For running included scripts
- **XCC Mixer v1.44** - Extract/inspect game files
- **Text Editor** - Edit INI configuration files

### Voxel Editing
- **VXLSE III v1.37** - Create and edit VXL voxel models
- **OS Voxel Viewer v1.7** - Preview VXL files with normals
- **OS HVA Builder v2.1** - Create animations for voxels

### 3D Modeling
- **Blender** + VXL addon - 3D modeling with VXL export
- **Blender VOX Export** - High-quality VOX export script (`scripts/blender_vox_export.py`)
- **MagicaVoxel** - View/edit VOX files before conversion

## Mental Omega Unit IDs

Common Mental Omega units you can modify:

| Unit ID | Name | Faction |
|---------|------|---------|
| ETNK | Bulldog Tank | Allied (USA) |
| MTNK | Grizzly Tank | Allied (vanilla RA2) |
| HTNK | Rhino Tank | Soviet |
| APOC | Apocalypse Tank | Soviet |
| LTNK | Lasher Tank | Soviet |

## Faction Names

Use these in `Owner=` to make units available to specific factions:

### Allied
- `British`
- `French`
- `Germans`
- `Americans`
- `Alliance`

### Soviet
- `Russians`
- `Confederation`
- `Africans`
- `Arabs`

### Yuri/Epsilon
- `YuriCountry`

### All Factions
```ini
Owner=British,French,Germans,Americans,Alliance,Russians,Confederation,Africans,Arabs,YuriCountry
```

## File Naming Convention

For RA2/YR units:
- Body: `UNITNAME.vxl` + `UNITNAME.hva`
- Turret: `UNITNAMETUR.vxl` + `UNITNAMETUR.hva`
- Barrel: `UNITNAMEBARL.vxl` + `UNITNAMEBARL.hva`

## Troubleshooting

### Unit is invisible
1. Check VXL/HVA section names match exactly
2. Ensure files are in the game folder (loose files, not just in MIX)
3. Verify VXL has non-zero dimensions (check with validation script)
4. Test with `Image=HTNK` first - if that works, your VXL is the problem

### Unit doesn't appear in build menu
1. Check `Owner=` includes your faction
2. Check `Prerequisite=` is empty or you have the required buildings
3. Verify unit ID is correct (ETNK for Bulldog, etc.)

### Model loads but looks wrong
1. Check remap bytes at VXL offset 32-33 are 16-31 (for team colors)
2. Verify normals mode is correct (2 for TS style, 4 for RA2)

## Credits

This guide was created while modding Mental Omega 3.3.6.
Mental Omega is a mod for Command & Conquer: Red Alert 2 Yuri's Revenge.

### Reference Files
- IronFist Example by Sleipnir64 and Dark_elf_2001
- VXL format from [tcrs/ra2ff](https://github.com/tcrs/ra2ff)
