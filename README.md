# Mental Omega 3.3.6 Custom Unit Modding Guide

A comprehensive guide for adding custom voxel units to Mental Omega 3.3.6 (Red Alert 2: Yuri's Revenge mod).

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Quick Start](#quick-start)
4. [Documentation Files](#documentation-files)
5. [Tools Required](#tools-required)

## Overview

This guide documents the process of adding a custom tank unit ("Nexus Devastator" - FTNKNEXUS) to Mental Omega 3.3.6. The same process can be applied to add any custom voxel unit.

### What We Accomplished

- Created a custom tank with rotating turret
- Exported VXL/HVA files from Blender
- Fixed section name mismatches between VXL and HVA files
- Packaged assets into a MIX file
- Configured unit stats via INI files

### Key Challenges Solved

1. **Protected MIX Files**: Mental Omega's core MIX files are protected. Solution: Use `INI/Map Code/Standard.ini` for rules.
2. **Section Name Mismatch**: Blender exports VXL with different section names than HVA. Solution: Use Python script to fix names.
3. **Invalid VXL Dimensions**: Initial export had 0x0x0 dimensions. Solution: Re-export with proper Blender settings.
4. **Turret Support**: Tanks need separate body and turret VXL files with matching naming convention.

## Project Structure

```
Mental Omega/
├── expandmo02.mix          # Custom assets MIX file
├── FTNKNEXUS.vxl           # Tank body voxel model
├── FTNKNEXUS.hva           # Tank body animation
├── FTNKNEXUSTUR.vxl        # Tank turret voxel model
├── FTNKNEXUSTUR.hva        # Tank turret animation
├── INI/
│   └── Map Code/
│       └── Standard.ini    # Custom unit definitions
└── Scripts/
    ├── create_mix.py       # MIX file creator
    ├── validate_vxl.py     # VXL file validator
    ├── fix_vxl_hva.py      # Section name fixer
    └── analyze_vxl.py      # VXL structure analyzer
```

## Quick Start

### Step 1: Export from Blender
1. Create your model in Blender with separate body and turret objects
2. Export body as `tankbody.vxl` and `tankbody.hva`
3. Export turret as `tankturret.vxl` and `tankturret.hva`

### Step 2: Validate and Fix Files
```bash
python validate_vxl.py      # Check for issues
python fix_section_names.py # Fix mismatched names
```

### Step 3: Rename Files
- `tankbody.vxl` -> `UNITNAME.vxl`
- `tankbody.hva` -> `UNITNAME.hva`
- `tankturret.vxl` -> `UNITNAMETUR.vxl`
- `tankturret.hva` -> `UNITNAMETUR.hva`

### Step 4: Create MIX File
```bash
python create_mix.py
```

### Step 5: Configure INI
Add unit definition to `INI/Map Code/Standard.ini`

### Step 6: Test
Copy `expandmo02.mix` to Mental Omega folder and launch game.

## Documentation Files

| File | Description |
|------|-------------|
| [01-VXL-HVA-Format.md](01-VXL-HVA-Format.md) | VXL/HVA file format specification |
| [02-MIX-File-Creation.md](02-MIX-File-Creation.md) | How to create MIX archive files |
| [03-INI-Configuration.md](03-INI-Configuration.md) | Unit INI configuration reference |
| [04-Troubleshooting.md](04-Troubleshooting.md) | Common issues and solutions |
| [05-Blender-Export.md](05-Blender-Export.md) | Blender VXL export settings |

## Tools Required

- **Python 3.x** - For running scripts
- **Blender** - 3D modeling with VXL export addon
- **XCC Mixer** (optional) - For inspecting MIX files
- **Voxel Section Editor** (optional) - For manual VXL editing
- **OS Voxel Viewer** (optional) - For previewing VXL files

## File Naming Convention

For RA2/YR units:
- Body: `UNITNAME.vxl` + `UNITNAME.hva`
- Turret: `UNITNAMETUR.vxl` + `UNITNAMETUR.hva`
- Barrel: `UNITNAMEBARL.vxl` + `UNITNAMEBARL.hva`

Example for our tank:
- `FTNKNEXUS.vxl` / `FTNKNEXUS.hva` (body)
- `FTNKNEXUSTUR.vxl` / `FTNKNEXUSTUR.hva` (turret)

## Credits

This guide was created while modding Mental Omega 3.3.6.
Mental Omega is a mod for Command & Conquer: Red Alert 2 Yuri's Revenge.
