# Blender VXL Export Guide

Guide for exporting VXL models from Blender for Red Alert 2 / Mental Omega.

> **NEW: High-Quality VOX Export** - See [VOX Export Workflow](#vox-export-workflow-recommended) for the recommended method that produces excellent quality voxel models!

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

---

## VOX Export Workflow (Recommended)

The **recommended workflow** for creating high-quality voxel models is to export from Blender to VOX format first, then convert to VXL. This produces excellent results with full color preservation.

### Why VOX First?

1. **Maximum Quality**: VOX supports up to 256×256×256 resolution
2. **Color Preservation**: Samples colors directly from textures/materials
3. **MagicaVoxel Compatible**: Can edit in MagicaVoxel before conversion
4. **Reliable Format**: Well-documented, widely supported format

### Step 1: Prepare Your Model

1. Import or create your model in Blender
2. Apply textures/materials with colors you want
3. Join all parts into a single mesh: Select all → `Ctrl+J`
4. Apply transforms: `Ctrl+A` → All Transforms

### Step 2: Export to VOX

Use the included high-quality VOX exporter script:

```bash
# Location of the script
scripts/blender_vox_export.py
```

**In Blender:**

1. Open the **Text Editor** panel
2. Click **Open** → Navigate to `scripts/blender_vox_export.py`
3. Select your mesh object in the 3D viewport
4. In the Text Editor, click **Run Script** (or press `Alt+P`)
5. Check the console for export progress and output path

**Export Settings (in script):**

- `max_resolution=256` - Maximum quality (default)
- Output path can be customized in the script

### Step 3: Preview in MagicaVoxel (Optional)

Open the exported `.vox` file in MagicaVoxel to:

- Verify the model looks correct
- Make manual edits if needed
- Adjust colors or add details

### Step 4: Convert VOX to VXL

Use the included converter script:

```bash
cd scripts
python vox_to_vxl.py path/to/yourmodel.vox
```

This creates:
- `yourmodel.vxl` - The voxel model
- `yourmodel.hva` - The animation file (identity transform)

**With custom output name:**

```bash
python vox_to_vxl.py model.vox MYUNIT.vxl Body
```

Arguments:
1. Input VOX file
2. Output VXL filename (optional)
3. Section name (optional, default: "Body")

### Step 5: Validate and Test

```bash
python validate_vxl.py MYUNIT.vxl
```

Then copy to Mental Omega folder and test in-game.

---

## Complete VOX Workflow Example

Here's a complete example exporting an Apocalypse Tank model:

### 1. In Blender

```
1. Import your model (OBJ, FBX, etc.)
2. Apply texture via UV mapping
3. Select all mesh parts
4. Join: Ctrl+J
5. Rename to "ApocalypseTank"
6. Apply transforms: Ctrl+A → All Transforms
```

### 2. Run VOX Export Script

```python
# In Blender's Text Editor, run:
scripts/blender_vox_export.py

# Output example:
# Exporting: ApocalypseTank
# Dimensions: 163 x 256 x 119
# Total voxels: 379,063
# Colors: 76
# SUCCESS! Exported to: apocalypse_tank.vox
```

### 3. Convert to VXL

```bash
python scripts/vox_to_vxl.py apocalypse_tank.vox FTNKAPOC.vxl Body
```

### 4. Deploy to Game

```bash
# Copy files to Mental Omega folder
copy FTNKAPOC.vxl "C:\Games\Mental Omega\"
copy FTNKAPOC.hva "C:\Games\Mental Omega\"
```

### 5. Configure INI

```ini
[APOC]
Image=FTNKAPOC
```

---

## VOX Export Script Reference

The `blender_vox_export.py` script features:

| Feature | Description |
|---------|-------------|
| **Max Resolution** | 256×256×256 voxels (VOX format maximum) |
| **Color Sampling** | Reads colors from UV-mapped textures |
| **Palette Generation** | Automatically builds optimized 255-color palette |
| **Progress Reporting** | Shows export progress for large models |
| **Texture Support** | Works with any image texture in material nodes |

### Customizing the Script

Edit the bottom of the script to change output settings:

```python
# Custom output path
output_path = r"C:\Users\YourName\Desktop\mymodel.vox"

# Custom resolution (lower = smaller file, faster export)
export_mesh_to_vox(output_path, max_resolution=128)
```

---

## Tips for Best Quality

1. **Use High-Res Textures**: The script samples colors from your texture
2. **Clean UV Mapping**: Ensure UVs correctly map to texture areas
3. **Proper Scale**: Model should be reasonably sized before export
4. **Single Material**: For best results, use one material with one texture
5. **Face Density**: More faces = more voxel samples = better detail
