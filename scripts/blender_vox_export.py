"""
High-Quality VOX Exporter for Blender
Exports Blender meshes to MagicaVoxel .vox format at maximum quality (255x255x255)

This is VXL-compatible (VXL format max dimension is 255 per axis).

Usage in Blender:
    1. Open Blender
    2. Go to Text Editor > Open > Select this file
    3. Select your mesh object
    4. Click "Run Script" or press Alt+P

The script exports to the same directory as the .blend file, or you can modify
the output_path variable at the bottom.

After export, you can:
    - Open in MagicaVoxel to view/edit
    - Convert to VXL using: python vox_to_vxl.py yourmodel.vox
"""

import bpy
import struct
from mathutils import Vector
from collections import defaultdict


def export_mesh_to_vox(output_path, max_resolution=255):
    """
    Export active mesh to VOX format at maximum quality.

    Args:
        output_path: Path for output .vox file
        max_resolution: Maximum voxel resolution (default 255 for VXL compatibility)

    Returns:
        True on success, False on failure
    """

    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH':
        print("ERROR: No mesh object selected!")
        print("Please select a mesh object and try again.")
        return False

    print(f"Exporting: {obj.name}")
    print("=" * 50)

    mesh = obj.data
    matrix = obj.matrix_world

    # Get world-space bounds
    verts_world = [matrix @ v.co for v in mesh.vertices]

    if not verts_world:
        print("ERROR: Mesh has no vertices!")
        return False

    min_x = min(v.x for v in verts_world)
    max_x = max(v.x for v in verts_world)
    min_y = min(v.y for v in verts_world)
    max_y = max(v.y for v in verts_world)
    min_z = min(v.z for v in verts_world)
    max_z = max(v.z for v in verts_world)

    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z
    max_size = max(size_x, size_y, size_z)

    if max_size == 0:
        print("ERROR: Model has zero size!")
        return False

    # Calculate voxel size for maximum quality
    voxel_size = max_size / max_resolution

    dim_x = min(256, max(1, int(size_x / voxel_size) + 1))
    dim_y = min(256, max(1, int(size_y / voxel_size) + 1))
    dim_z = min(256, max(1, int(size_z / voxel_size) + 1))

    print(f"Model bounds: {size_x:.2f} x {size_y:.2f} x {size_z:.2f}")
    print(f"VOX dimensions: {dim_x} x {dim_y} x {dim_z}")
    print(f"Voxel size: {voxel_size:.4f}")

    # Get UV layer and texture for color sampling
    uv_layer = mesh.uv_layers.active
    tex_image = None
    tex_pixels = None
    tex_w, tex_h = 0, 0

    if mesh.materials:
        mat = mesh.materials[0]
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    tex_image = node.image
                    tex_w, tex_h = tex_image.size
                    tex_pixels = list(tex_image.pixels)
                    print(f"Found texture: {tex_image.name} ({tex_w}x{tex_h})")
                    break

    if not tex_image:
        print("No texture found - using default gray color")

    # Build voxel data from face centers
    voxels = {}  # (x,y,z) -> (r,g,b)
    palette_map = {}  # (r,g,b) -> index
    palette = [(0, 0, 0)]  # Index 0 is unused in VOX format

    print(f"\nProcessing {len(mesh.polygons)} faces...")
    total_faces = len(mesh.polygons)

    for i, poly in enumerate(mesh.polygons):
        # Progress indicator
        if i % 10000 == 0:
            percent = (i / total_faces) * 100
            print(f"  Progress: {i}/{total_faces} ({percent:.1f}%)")

        # Get face center in world space
        center = matrix @ poly.center

        # Convert to voxel coordinates
        vx = int((center.x - min_x) / voxel_size)
        vy = int((center.y - min_y) / voxel_size)
        vz = int((center.z - min_z) / voxel_size)

        # Clamp to valid range
        vx = max(0, min(dim_x - 1, vx))
        vy = max(0, min(dim_y - 1, vy))
        vz = max(0, min(dim_z - 1, vz))

        # Get color from texture via UV mapping
        r, g, b = 128, 128, 128  # Default gray

        if uv_layer and tex_pixels and tex_w > 0:
            loop_idx = poly.loop_indices[0]
            uv = uv_layer.data[loop_idx].uv

            px = int(uv.x * tex_w) % tex_w
            py = int(uv.y * tex_h) % tex_h

            pixel_idx = (py * tex_w + px) * 4
            if pixel_idx + 2 < len(tex_pixels):
                r = int(tex_pixels[pixel_idx] * 255)
                g = int(tex_pixels[pixel_idx + 1] * 255)
                b = int(tex_pixels[pixel_idx + 2] * 255)

        voxels[(vx, vy, vz)] = (r, g, b)

    print(f"\nTotal unique voxel positions: {len(voxels)}")

    # Build color palette (VOX supports 255 colors, indices 1-255)
    print("Building color palette...")
    unique_colors = list(set(voxels.values()))

    if len(unique_colors) > 255:
        print(f"Warning: {len(unique_colors)} colors found, reducing to 255...")
        # Simple reduction - take most common colors
        color_counts = defaultdict(int)
        for color in voxels.values():
            color_counts[color] += 1
        unique_colors = sorted(color_counts.keys(), key=lambda c: color_counts[c], reverse=True)[:255]

    for i, color in enumerate(unique_colors):
        palette_map[color] = i + 1  # VOX uses 1-indexed colors
        palette.append(color)

    # Pad palette to 256 entries
    while len(palette) < 256:
        palette.append((0, 0, 0))

    print(f"Unique colors in palette: {len(unique_colors)}")

    # Map voxels to palette indices
    voxel_list = []
    for (x, y, z), color in voxels.items():
        if color in palette_map:
            idx = palette_map[color]
        else:
            # Find closest color in palette
            min_dist = float('inf')
            idx = 1
            for c, i in palette_map.items():
                dist = sum((a-b)**2 for a, b in zip(color, c))
                if dist < min_dist:
                    min_dist = dist
                    idx = i
        voxel_list.append((x, y, z, idx))

    # Build VOX file structure
    print("\nWriting VOX file...")

    # SIZE chunk - model dimensions
    size_content = struct.pack('<III', dim_x, dim_y, dim_z)
    size_chunk = b'SIZE' + struct.pack('<II', 12, 0) + size_content

    # XYZI chunk - voxel positions and colors
    xyzi_content = struct.pack('<I', len(voxel_list))
    for x, y, z, c in voxel_list:
        xyzi_content += struct.pack('<BBBB', x, y, z, c)
    xyzi_chunk = b'XYZI' + struct.pack('<II', len(xyzi_content), 0) + xyzi_content

    # RGBA chunk - color palette
    rgba_content = b''
    for r, g, b in palette[1:]:  # Skip index 0
        rgba_content += struct.pack('<BBBB', r, g, b, 255)
    # Pad to exactly 256 colors
    while len(rgba_content) < 256 * 4:
        rgba_content += struct.pack('<BBBB', 0, 0, 0, 255)
    rgba_chunk = b'RGBA' + struct.pack('<II', 256 * 4, 0) + rgba_content

    # MAIN chunk - contains all other chunks
    children = size_chunk + xyzi_chunk + rgba_chunk
    main_chunk = b'MAIN' + struct.pack('<II', 0, len(children)) + children

    # Write complete VOX file
    with open(output_path, 'wb') as f:
        f.write(b'VOX ')  # Magic number
        f.write(struct.pack('<I', 150))  # Version
        f.write(main_chunk)

    # Calculate file size
    import os
    file_size = os.path.getsize(output_path)

    print("=" * 50)
    print(f"SUCCESS! Exported to: {output_path}")
    print(f"  Dimensions: {dim_x} x {dim_y} x {dim_z}")
    print(f"  Voxels: {len(voxel_list):,}")
    print(f"  Colors: {len(unique_colors)}")
    print(f"  File size: {file_size:,} bytes")
    print("=" * 50)

    return True


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    import os

    # Get output path - same directory as blend file, or Desktop
    blend_path = bpy.data.filepath
    if blend_path:
        output_dir = os.path.dirname(blend_path)
        base_name = os.path.splitext(os.path.basename(blend_path))[0]
    else:
        output_dir = os.path.expanduser("~/Desktop")
        base_name = "blender_export"

    # Or specify a custom output path here:
    # output_path = r"C:\Users\YourName\Desktop\mymodel.vox"

    output_path = os.path.join(output_dir, f"{base_name}.vox")

    print("\n" + "=" * 50)
    print("HIGH-QUALITY VOX EXPORTER")
    print("=" * 50 + "\n")

    export_mesh_to_vox(output_path, max_resolution=256)
