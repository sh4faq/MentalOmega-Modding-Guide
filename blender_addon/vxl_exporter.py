# VXL Exporter for Blender
# Exports Blender mesh to VXL format for Red Alert 2/Yuri's Revenge/Mental Omega
#
# Based on working IronFist (wrmn.vxl) format analysis
#
# Installation:
#   1. Open Blender
#   2. Edit > Preferences > Add-ons > Install
#   3. Select this file
#   4. Enable "Export: VXL Exporter"
#
# Usage:
#   1. Select your mesh object
#   2. File > Export > VXL for RA2 (.vxl)

bl_info = {
    "name": "VXL Exporter for RA2",
    "author": "Mental Omega Modding Guide",
    "version": (1, 1, 0),
    "blender": (2, 80, 0),
    "location": "File > Export > VXL for RA2",
    "description": "Export mesh to VXL format for Red Alert 2/Mental Omega",
    "category": "Import-Export",
}

import bpy
import struct
import math
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, IntProperty, FloatProperty

def voxelize_mesh(obj, resolution):
    """Convert mesh to voxel grid using ray casting."""
    import bmesh
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    mesh = obj.data

    # Get world-space bounding box
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    bbox_min = Vector((min(c.x for c in bbox_corners),
                       min(c.y for c in bbox_corners),
                       min(c.z for c in bbox_corners)))
    bbox_max = Vector((max(c.x for c in bbox_corners),
                       max(c.y for c in bbox_corners),
                       max(c.z for c in bbox_corners)))

    size = bbox_max - bbox_min
    max_dim = max(size.x, size.y, size.z)

    if max_dim == 0:
        return None, 0, 0, 0, bbox_min, bbox_max

    voxel_size = max_dim / resolution

    dim_x = max(1, int(math.ceil(size.x / voxel_size)))
    dim_y = max(1, int(math.ceil(size.y / voxel_size)))
    dim_z = max(1, int(math.ceil(size.z / voxel_size)))

    # Limit to VXL max (255)
    dim_x = min(dim_x, 255)
    dim_y = min(dim_y, 255)
    dim_z = min(dim_z, 255)

    # Create voxel grid
    voxels = [[[False for _ in range(dim_z)] for _ in range(dim_y)] for _ in range(dim_x)]

    # Build BVH tree for ray casting
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.transform(obj.matrix_world)
    bvh = BVHTree.FromBMesh(bm)

    # Voxelize by checking if points are inside mesh
    for x in range(dim_x):
        for y in range(dim_y):
            for z in range(dim_z):
                px = bbox_min.x + (x + 0.5) * voxel_size
                py = bbox_min.y + (y + 0.5) * voxel_size
                pz = bbox_min.z + (z + 0.5) * voxel_size
                point = Vector((px, py, pz))

                # Ray cast to check if inside
                for direction in [Vector((1,0,0)), Vector((-1,0,0)),
                                  Vector((0,1,0)), Vector((0,-1,0)),
                                  Vector((0,0,1)), Vector((0,0,-1))]:
                    hit, normal, index, dist = bvh.ray_cast(point, direction)
                    if hit and dist < voxel_size * 2:
                        voxels[x][y][z] = True
                        break

    bm.free()

    # Calculate actual bounds based on voxel grid
    scale = 0.083333  # Standard VXL scale (1/12)
    min_bounds = (
        -(dim_x / 2.0) / scale,
        -(dim_y / 2.0) / scale,
        0.0
    )
    max_bounds = (
        (dim_x / 2.0) / scale,
        (dim_y / 2.0) / scale,
        dim_z / scale
    )

    return voxels, dim_x, dim_y, dim_z, min_bounds, max_bounds

def calculate_normal_index(x, y, z, voxels, dim_x, dim_y, dim_z):
    """Calculate RA2 normal index based on exposed faces."""
    exposed = [False] * 6

    if x >= dim_x - 1 or not voxels[x+1][y][z]: exposed[0] = True  # +X
    if x <= 0 or not voxels[x-1][y][z]: exposed[1] = True          # -X
    if y >= dim_y - 1 or not voxels[x][y+1][z]: exposed[2] = True  # +Y
    if y <= 0 or not voxels[x][y-1][z]: exposed[3] = True          # -Y
    if z >= dim_z - 1 or not voxels[x][y][z+1]: exposed[4] = True  # +Z (top)
    if z <= 0 or not voxels[x][y][z-1]: exposed[5] = True          # -Z (bottom)

    # RA2 normal indices (Tiberian Sun style = mode 2)
    if exposed[4]: return 0   # Top
    if exposed[5]: return 12  # Bottom
    if exposed[0]: return 6   # +X
    if exposed[1]: return 18  # -X
    if exposed[2]: return 3   # +Y
    if exposed[3]: return 21  # -Y
    return 0

def create_vxl(voxels, dim_x, dim_y, dim_z, min_bounds, max_bounds, section_name="Body"):
    """
    Create VXL file matching working wrmn.vxl format exactly.

    Format verified against IronFist wrmn.vxl (44101 bytes):
    - Header: 34 bytes
    - Palette: 768 bytes
    - Limb Header: 28 bytes (starts at offset 802)
    - Body Data: variable (span offsets + voxel data)
    - Tailer: 92 bytes
    """

    # Build span data (matching wrmn.vxl format)
    num_columns = dim_x * dim_y
    span_start_offsets = []
    span_end_offsets = []
    voxel_data = bytearray()

    for y in range(dim_y):
        for x in range(dim_x):
            has_voxels = any(voxels[x][y][z] for z in range(dim_z))

            if not has_voxels:
                span_start_offsets.append(0xFFFFFFFF)
                span_end_offsets.append(0xFFFFFFFF)
                continue

            col_start = len(voxel_data)
            z = 0

            while z < dim_z:
                # Skip empty voxels
                while z < dim_z and not voxels[x][y][z]:
                    z += 1
                if z >= dim_z:
                    break

                skip_count = z

                # Count solid voxels
                span_start_z = z
                while z < dim_z and voxels[x][y][z]:
                    z += 1
                span_count = z - span_start_z

                # Write span: skip, count, [color, normal] * count, count (duplicate!)
                voxel_data.append(skip_count)
                voxel_data.append(span_count)

                for vz in range(span_start_z, span_start_z + span_count):
                    color = 100  # Default model color
                    normal = calculate_normal_index(x, y, vz, voxels, dim_x, dim_y, dim_z)
                    voxel_data.append(color)
                    voxel_data.append(normal)

                # Duplicate count (REQUIRED by game engine!)
                voxel_data.append(span_count)

            # End marker
            remaining = dim_z - z if z < dim_z else 0
            voxel_data.append(remaining)
            voxel_data.append(0)

            col_end = len(voxel_data)
            span_start_offsets.append(col_start)
            span_end_offsets.append(col_end)

    # Build body data (offsets + voxel data)
    body_data = bytearray()

    # Span start offsets (4 bytes each)
    for offset in span_start_offsets:
        body_data.extend(struct.pack('<I', offset))

    # Span end offsets (4 bytes each)
    for offset in span_end_offsets:
        body_data.extend(struct.pack('<I', offset))

    # Voxel span data
    body_data.extend(voxel_data)
    body_size = len(body_data)

    # === Build complete VXL file ===
    vxl_data = bytearray()

    # --- Header (34 bytes) ---
    vxl_data.extend(b'Voxel Animation\x00')  # 16 bytes: file type
    vxl_data.extend(struct.pack('<I', 1))     # 4 bytes: unknown (always 1)
    vxl_data.extend(struct.pack('<I', 1))     # 4 bytes: num limbs
    vxl_data.extend(struct.pack('<I', 1))     # 4 bytes: num limbs (duplicate)
    vxl_data.extend(struct.pack('<I', body_size))  # 4 bytes: body size
    vxl_data.append(16)  # 1 byte: remap start
    vxl_data.append(31)  # 1 byte: remap end

    # --- Palette (768 bytes) ---
    # Standard RA2 grayscale palette with team color ramp at 16-31
    for i in range(256):
        if 16 <= i <= 31:
            # Team color gradient
            intensity = int((i - 16) * 16)
            vxl_data.extend(bytes([intensity, intensity // 2, intensity // 4]))
        else:
            vxl_data.extend(bytes([i, i, i]))

    # --- Limb Header (28 bytes, starts at offset 802) ---
    # Section name MUST be exactly 16 bytes and match HVA
    name_bytes = section_name.encode('ascii')[:16].ljust(16, b'\x00')
    vxl_data.extend(name_bytes)           # 16 bytes: section name
    vxl_data.extend(struct.pack('<I', 0)) # 4 bytes: limb number (0)
    vxl_data.extend(struct.pack('<I', 1)) # 4 bytes: unknown1 (1)
    vxl_data.extend(struct.pack('<I', 0)) # 4 bytes: unknown2 (0)

    # --- Body Data (variable) ---
    vxl_data.extend(body_data)

    # --- Tailer (92 bytes) ---
    # Offsets into body data
    vxl_data.extend(struct.pack('<I', 0))                    # Span start offset (0)
    vxl_data.extend(struct.pack('<I', num_columns * 4))      # Span end offset
    vxl_data.extend(struct.pack('<I', num_columns * 8))      # Span data offset

    # Scale (0.083333 = 1/12, standard for RA2)
    vxl_data.extend(struct.pack('<f', 0.083333))

    # Transform matrix (identity, 12 floats = 48 bytes)
    for val in [1.0, 0.0, 0.0, 0.0,   # Row 1
                0.0, 1.0, 0.0, 0.0,   # Row 2
                0.0, 0.0, 1.0, 0.0]:  # Row 3
        vxl_data.extend(struct.pack('<f', val))

    # MinBounds (3 floats = 12 bytes)
    vxl_data.extend(struct.pack('<fff', min_bounds[0], min_bounds[1], min_bounds[2]))

    # MaxBounds (3 floats = 12 bytes)
    vxl_data.extend(struct.pack('<fff', max_bounds[0], max_bounds[1], max_bounds[2]))

    # Dimensions (3 bytes)
    vxl_data.append(dim_x)
    vxl_data.append(dim_y)
    vxl_data.append(dim_z)

    # Normals mode (1 byte) - 2 = Tiberian Sun style
    vxl_data.append(2)

    return bytes(vxl_data), name_bytes

def create_hva(section_name_bytes, filename="EXPORT"):
    """
    Create HVA file with EXACT same section name as VXL.

    Format: 88 bytes total
    - Header: 24 bytes (filename + frame count + section count)
    - Section name: 16 bytes (MUST match VXL exactly!)
    - Transform matrix: 48 bytes (identity)
    """
    hva_data = bytearray()

    # Header (24 bytes)
    hva_data.extend(filename.encode('ascii')[:16].ljust(16, b'\x00'))  # 16 bytes: filename
    hva_data.extend(struct.pack('<I', 1))  # 4 bytes: 1 frame
    hva_data.extend(struct.pack('<I', 1))  # 4 bytes: 1 section

    # Section name (16 bytes) - MUST match VXL exactly!
    hva_data.extend(section_name_bytes)

    # Transform matrix (48 bytes) - identity
    for val in [1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0]:
        hva_data.extend(struct.pack('<f', val))

    return bytes(hva_data)

class ExportVXL(bpy.types.Operator, ExportHelper):
    """Export mesh to VXL format for Red Alert 2/Mental Omega"""
    bl_idname = "export_scene.vxl"
    bl_label = "Export VXL"
    bl_options = {'PRESET'}

    filename_ext = ".vxl"
    filter_glob: StringProperty(default="*.vxl", options={'HIDDEN'})

    resolution: IntProperty(
        name="Resolution",
        description="Voxel resolution (32-64 recommended for tanks)",
        default=48,
        min=16,
        max=128
    )

    section_name: StringProperty(
        name="Section Name",
        description="VXL section name (Body for hull, turret for turret)",
        default="Body"
    )

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object first")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Voxelizing {obj.name} at resolution {self.resolution}...")

        # Voxelize mesh
        result = voxelize_mesh(obj, self.resolution)
        if result[0] is None:
            self.report({'ERROR'}, "Failed to voxelize mesh - check object has geometry")
            return {'CANCELLED'}

        voxels, dim_x, dim_y, dim_z, min_bounds, max_bounds = result

        # Count filled voxels
        filled = sum(1 for x in range(dim_x) for y in range(dim_y) for z in range(dim_z) if voxels[x][y][z])

        if filled == 0:
            self.report({'ERROR'}, "No voxels generated - try increasing resolution")
            return {'CANCELLED'}

        # Create VXL (returns data and section name bytes)
        vxl_data, section_name_bytes = create_vxl(
            voxels, dim_x, dim_y, dim_z,
            min_bounds, max_bounds,
            self.section_name
        )

        # Write VXL
        with open(self.filepath, 'wb') as f:
            f.write(vxl_data)

        # Create and write HVA with matching section name
        import os
        basename = os.path.splitext(os.path.basename(self.filepath))[0]
        hva_path = self.filepath.replace('.vxl', '.hva')
        hva_data = create_hva(section_name_bytes, basename.upper())

        with open(hva_path, 'wb') as f:
            f.write(hva_data)

        self.report({'INFO'},
            f"Exported: {dim_x}x{dim_y}x{dim_z} voxels ({filled} filled), "
            f"VXL: {len(vxl_data)} bytes, HVA: {len(hva_data)} bytes")

        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(ExportVXL.bl_idname, text="VXL for RA2 (.vxl)")

def register():
    bpy.utils.register_class(ExportVXL)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportVXL)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
