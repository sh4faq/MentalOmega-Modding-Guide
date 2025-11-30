# VXL Exporter for Blender
# Exports Blender mesh to VXL format for Red Alert 2/Yuri's Revenge
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
    "name": "VXL Exporter",
    "author": "Mental Omega Modding Guide",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Export > VXL for RA2",
    "description": "Export mesh to VXL format for Red Alert 2/Yuri's Revenge",
    "category": "Import-Export",
}

import bpy
import struct
import math
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, IntProperty, FloatProperty

def voxelize_mesh(obj, resolution):
    """Convert mesh to voxel grid."""
    import bmesh
    from mathutils import Vector

    # Get mesh data
    mesh = obj.data

    # Get bounding box
    bbox_min = Vector((float('inf'), float('inf'), float('inf')))
    bbox_max = Vector((float('-inf'), float('-inf'), float('-inf')))

    for v in mesh.vertices:
        world_co = obj.matrix_world @ v.co
        bbox_min.x = min(bbox_min.x, world_co.x)
        bbox_min.y = min(bbox_min.y, world_co.y)
        bbox_min.z = min(bbox_min.z, world_co.z)
        bbox_max.x = max(bbox_max.x, world_co.x)
        bbox_max.y = max(bbox_max.y, world_co.y)
        bbox_max.z = max(bbox_max.z, world_co.z)

    # Calculate dimensions
    size = bbox_max - bbox_min
    max_dim = max(size.x, size.y, size.z)

    if max_dim == 0:
        return None, 0, 0, 0

    voxel_size = max_dim / resolution

    dim_x = max(1, int(math.ceil(size.x / voxel_size)))
    dim_y = max(1, int(math.ceil(size.y / voxel_size)))
    dim_z = max(1, int(math.ceil(size.z / voxel_size)))

    # Limit dimensions to 255 (VXL max)
    dim_x = min(dim_x, 255)
    dim_y = min(dim_y, 255)
    dim_z = min(dim_z, 255)

    # Create voxel grid
    voxels = [[[False for _ in range(dim_z)] for _ in range(dim_y)] for _ in range(dim_x)]

    # Sample mesh at voxel centers
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.transform(obj.matrix_world)

    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromBMesh(bm)

    for x in range(dim_x):
        for y in range(dim_y):
            for z in range(dim_z):
                # Voxel center in world space
                px = bbox_min.x + (x + 0.5) * voxel_size
                py = bbox_min.y + (y + 0.5) * voxel_size
                pz = bbox_min.z + (z + 0.5) * voxel_size

                point = Vector((px, py, pz))

                # Check if point is inside mesh using ray casting
                # Cast rays in multiple directions and count intersections
                inside = False
                for direction in [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]:
                    hit, normal, index, dist = bvh.ray_cast(point, direction)
                    if hit:
                        inside = True
                        break

                if inside:
                    voxels[x][y][z] = True

    bm.free()

    return voxels, dim_x, dim_y, dim_z

def calculate_normal_index(x, y, z, voxels, dim_x, dim_y, dim_z):
    """Calculate normal index based on exposed faces."""
    # Check which faces are exposed
    exposed = [False] * 6  # +X, -X, +Y, -Y, +Z, -Z

    if x >= dim_x - 1 or not voxels[x+1][y][z]: exposed[0] = True  # +X
    if x <= 0 or not voxels[x-1][y][z]: exposed[1] = True  # -X
    if y >= dim_y - 1 or not voxels[x][y+1][z]: exposed[2] = True  # +Y
    if y <= 0 or not voxels[x][y-1][z]: exposed[3] = True  # -Y
    if z >= dim_z - 1 or not voxels[x][y][z+1]: exposed[4] = True  # +Z (top)
    if z <= 0 or not voxels[x][y][z-1]: exposed[5] = True  # -Z (bottom)

    # RA2 normal indices (simplified)
    if exposed[4]: return 0   # Top
    if exposed[5]: return 12  # Bottom
    if exposed[0]: return 6   # +X
    if exposed[1]: return 18  # -X
    if exposed[2]: return 3   # +Y
    if exposed[3]: return 21  # -Y
    return 0

def create_vxl(voxels, dim_x, dim_y, dim_z, section_name="Body"):
    """Create VXL file data from voxel grid."""

    # Build span data
    num_columns = dim_x * dim_y
    span_start_offsets = []
    span_end_offsets = []
    voxel_data = bytearray()

    for y in range(dim_y):
        for x in range(dim_x):
            # Check if column has any voxels
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

                # Write span
                voxel_data.append(skip_count)
                voxel_data.append(span_count)

                for vz in range(span_start_z, span_start_z + span_count):
                    color = 100  # Default color
                    normal = calculate_normal_index(x, y, vz, voxels, dim_x, dim_y, dim_z)
                    voxel_data.append(color)
                    voxel_data.append(normal)

                # Duplicate count (required!)
                voxel_data.append(span_count)

            # End marker
            remaining = dim_z - z if z < dim_z else 0
            voxel_data.append(remaining)
            voxel_data.append(0)

            col_end = len(voxel_data)
            span_start_offsets.append(col_start)
            span_end_offsets.append(col_end)

    # Build body data
    body_data = bytearray()

    for offset in span_start_offsets:
        body_data.extend(struct.pack('<I', offset))

    for offset in span_end_offsets:
        body_data.extend(struct.pack('<I', offset))

    body_data.extend(voxel_data)
    body_size = len(body_data)

    # Build VXL file
    vxl_data = bytearray()

    # Header (34 bytes)
    vxl_data.extend(b'Voxel Animation\x00')  # 16 bytes
    vxl_data.extend(struct.pack('<I', 1))     # Unknown (always 1)
    vxl_data.extend(struct.pack('<I', 1))     # Number of limbs
    vxl_data.extend(struct.pack('<I', 1))     # Number of limbs (duplicate)
    vxl_data.extend(struct.pack('<I', body_size))  # Body size
    vxl_data.append(16)  # Remap start
    vxl_data.append(31)  # Remap end

    # Palette (768 bytes) - default RA2 palette
    for i in range(256):
        if 16 <= i <= 31:
            # Team color ramp
            vxl_data.extend(bytes([i * 8, i * 4, i * 2]))
        else:
            vxl_data.extend(bytes([i, i, i]))

    # Limb header (28 bytes)
    name_bytes = section_name.encode('ascii')[:16].ljust(16, b'\x00')
    vxl_data.extend(name_bytes)
    vxl_data.extend(struct.pack('<I', 0))  # Limb number
    vxl_data.extend(struct.pack('<I', 1))  # Unknown 1
    vxl_data.extend(struct.pack('<I', 0))  # Unknown 2

    # Body data
    vxl_data.extend(body_data)

    # Tailer (92 bytes)
    vxl_data.extend(struct.pack('<I', 0))  # Span start offset
    vxl_data.extend(struct.pack('<I', num_columns * 4))  # Span end offset
    vxl_data.extend(struct.pack('<I', num_columns * 8))  # Span data offset
    vxl_data.extend(struct.pack('<f', 0.083333))  # Scale

    # Transform matrix (identity)
    for val in [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]:
        vxl_data.extend(struct.pack('<f', val))

    # Min bounds
    vxl_data.extend(struct.pack('<fff', 0.0, 0.0, 0.0))

    # Max bounds
    vxl_data.extend(struct.pack('<fff', float(dim_x), float(dim_y), float(dim_z)))

    # Dimensions
    vxl_data.append(dim_x)
    vxl_data.append(dim_y)
    vxl_data.append(dim_z)
    vxl_data.append(2)  # Normals mode (2 = TS style)

    return bytes(vxl_data)

def create_hva(section_name="Body"):
    """Create HVA file data."""
    hva_data = bytearray()

    # Header
    hva_data.extend(section_name.encode('ascii')[:16].ljust(16, b'\x00'))
    hva_data.extend(struct.pack('<I', 1))  # 1 frame
    hva_data.extend(struct.pack('<I', 1))  # 1 section

    # Section name
    hva_data.extend(section_name.encode('ascii')[:16].ljust(16, b'\x00'))

    # Identity matrix
    for val in [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]:
        hva_data.extend(struct.pack('<f', val))

    return bytes(hva_data)

class ExportVXL(bpy.types.Operator, ExportHelper):
    """Export mesh to VXL format for Red Alert 2"""
    bl_idname = "export_scene.vxl"
    bl_label = "Export VXL"
    bl_options = {'PRESET'}

    filename_ext = ".vxl"
    filter_glob: StringProperty(default="*.vxl", options={'HIDDEN'})

    resolution: IntProperty(
        name="Resolution",
        description="Voxel resolution (higher = more detail, larger file)",
        default=32,
        min=8,
        max=128
    )

    section_name: StringProperty(
        name="Section Name",
        description="VXL section name (use 'Body' for main, 'turret' for turret)",
        default="Body"
    )

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}

        # Voxelize mesh
        voxels, dim_x, dim_y, dim_z = voxelize_mesh(obj, self.resolution)

        if voxels is None:
            self.report({'ERROR'}, "Failed to voxelize mesh")
            return {'CANCELLED'}

        # Create VXL
        vxl_data = create_vxl(voxels, dim_x, dim_y, dim_z, self.section_name)

        with open(self.filepath, 'wb') as f:
            f.write(vxl_data)

        # Create HVA
        hva_path = self.filepath.replace('.vxl', '.hva')
        hva_data = create_hva(self.section_name)

        with open(hva_path, 'wb') as f:
            f.write(hva_data)

        self.report({'INFO'}, f"Exported VXL ({dim_x}x{dim_y}x{dim_z}) and HVA")
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
