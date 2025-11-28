# Blender VXL Export Guide

Guide for exporting VXL models from Blender for Red Alert 2 / Mental Omega.

---

## Prerequisites

### Required Addon

Install a Blender VXL export addon. Common options:
- **Voxel Plugin for Blender** by various authors
- Search "Blender VXL exporter RA2" for current versions

### Blender Version

- Blender 2.8x - 3.x recommended
- Check addon compatibility with your Blender version

---

## Model Setup

### Scale and Dimensions

RA2 voxel units have specific size expectations:

| Unit Type | Typical Size (voxels) |
|-----------|----------------------|
| Infantry | 10-15 x 10-15 x 20-30 |
| Light Vehicle | 20-30 x 15-25 x 10-20 |
| Tank | 30-50 x 20-40 x 15-25 |
| Heavy Tank | 40-70 x 30-50 x 20-35 |
| Building | Varies widely |

**Important:** Your model dimensions become the VXL dimensions. If Blender shows 0 dimensions, the export will fail!

### Applying Transforms

Before export, ALWAYS apply transforms:

1. Select your object
2. Press `Ctrl+A`
3. Select "All Transforms"

This ensures scale, rotation, and location are baked into the mesh.

### Origin Point

The origin point becomes the unit's center:
- For vehicles: Center-bottom of the model
- For turrets: Center of rotation point

---

## Creating Body and Turret

### Separate Objects

For tanks with rotating turrets, create two separate objects:

1. **Body**: Main hull/chassis (name it "body" or similar)
2. **Turret**: Rotating gun platform (name it "turret")

### Turret Positioning

Position the turret at the origin (0,0,0) in its own local space:
- The turret rotates around its local origin
- Offset from body is handled by the game

---

## Color Palette

RA2 uses indexed color palettes. Key indices:

| Index Range | Purpose |
|-------------|---------|
| 0 | Transparent |
| 1-15 | Shadow colors |
| 16-31 | **Team/Remap colors** |
| 32-255 | Model colors |

### Team Colors

To support faction colors, use palette indices 16-31 for areas that should change color (unit markings, panels, etc.).

---

## Export Settings

### VXL Export

1. Select the object to export
2. File > Export > VXL (or your addon's export option)
3. Settings:
   - **Filename**: Use uppercase (UNITNAME.vxl)
   - **Section Name**: Set to "body" or "turret"
   - **Scale**: Usually 1.0 (adjust if model is too big/small in game)
   - **Normals**: Let addon calculate

### HVA Export

Export HVA immediately after VXL:
1. Same object selected
2. File > Export > HVA
3. **Critical**: Section name MUST match VXL section name!

---

## Common Export Issues

### Issue: Zero Dimensions

**Symptom**: VXL has 0x0x0 dimensions

**Causes**:
- Object has no geometry
- Scale not applied
- Object is hidden or on wrong layer
- Exporting empty object

**Solution**:
1. Verify object has actual mesh data
2. Apply all transforms (`Ctrl+A` > All Transforms)
3. Check object is visible and selected
4. Try exporting to a simple test location first

### Issue: Section Name Mismatch

**Symptom**: Blender exports with names like "model_LOD0" or "Cube.001"

**Solution**:
1. Rename object in Blender to desired section name
2. Or use Python script to fix after export

### Issue: Model Too Big/Small

**Symptom**: Model is gigantic or tiny in game

**Solution**:
1. Scale model in Blender before export
2. Apply scale (`Ctrl+A` > Scale)
3. Use export scale setting if available

### Issue: Wrong Orientation

**Symptom**: Model faces wrong direction or is rotated

**RA2 Orientation**:
- +X = Right
- +Y = Forward (direction unit faces)
- +Z = Up

**Solution**:
1. Rotate model in Blender to face +Y
2. Apply rotation (`Ctrl+A` > Rotation)

---

## Step-by-Step Tank Export

### 1. Body Export

1. Select body mesh
2. Rename object to "body" in outliner
3. Apply transforms: `Ctrl+A` > All Transforms
4. Set origin: Right-click > Set Origin > Origin to Center of Mass
5. Export VXL:
   - Filename: `tankbody.vxl`
   - Section name: `body`
6. Export HVA:
   - Filename: `tankbody.hva`
   - Section name: `body` (MUST MATCH!)

### 2. Turret Export

1. Select turret mesh
2. Rename object to "turret" in outliner
3. Move turret to origin (0,0,0)
4. Apply transforms
5. Export VXL:
   - Filename: `tankturret.vxl`
   - Section name: `turret`
6. Export HVA:
   - Filename: `tankturret.hva`
   - Section name: `turret`

### 3. Post-Export

1. Validate both VXL files:
   ```bash
   python validate_vxl.py tankbody.vxl
   python validate_vxl.py tankturret.vxl
   ```

2. Fix section names if needed:
   ```bash
   python fix_section_names.py
   ```

3. Rename to final names:
   - `tankbody.vxl` -> `FTNKNEXUS.vxl`
   - `tankbody.hva` -> `FTNKNEXUS.hva`
   - `tankturret.vxl` -> `FTNKNEXUSTUR.vxl`
   - `tankturret.hva` -> `FTNKNEXUSTUR.hva`

---

## Animation (Advanced)

### Static Models

For units without animation:
- Export single-frame HVA
- HVA contains identity transform matrix

### Animated Models

For walking mechs, turret recoil, etc.:
- Create keyframe animation in Blender
- Export HVA with multiple frames
- Game plays through frames based on unit state

### Multi-Section Models

For complex units (mech with arms, legs):
1. Create separate objects for each section
2. Name appropriately: body, turret, barrel, etc.
3. Export each as separate VXL/HVA pair
4. Configure in INI with appropriate settings

---

## Verification Checklist

Before testing in game:

- [ ] VXL file size > 1KB (not empty)
- [ ] Dimensions are non-zero (check with validate script)
- [ ] Section names match between VXL and HVA
- [ ] Files are uppercase: `UNITNAME.vxl`
- [ ] Both VXL and HVA exported
- [ ] Turret files end with TUR: `UNITNAMETUR.vxl`
- [ ] Files added to MIX archive
- [ ] INI configuration complete

---

## Alternative Tools

If Blender export fails, try:

### VXLSE (Voxel Section Editor)
- Windows application
- Can import/export VXL
- Manual voxel editing

### OS Voxel Viewer
- Preview VXL files
- Verify structure

### MagicaVoxel + Converter
- Create in MagicaVoxel
- Convert to RA2 VXL format

### XCC Mixer
- Inspect existing game VXL files
- Extract reference models
