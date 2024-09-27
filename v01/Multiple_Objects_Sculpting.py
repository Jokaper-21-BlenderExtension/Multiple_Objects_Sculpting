import bpy
import json

bl_info = {
    "name": "Multi-Object Sculpting",
    "blender": (4, 2, 0),
    "category": "Sculpt",
}

bl_info = {
    "name": "Multi-Object Sculpting",
    "author": "Ananthan (Jokaper)",
    "version": (4, 2, 0),
    "location": "View3D > N-Panel",
    "description": "Multiple Objects Sculpting",
    "category": "AJO",  # Category in which it appears, e.g., Object, Render, etc.
}


class MULTI_SCULPT_OT_sculpt_objects(bpy.types.Operator):
    """Sculpt Multiple Objects"""
    bl_idname = "sculpt.multi_sculpt"
    bl_label = "Sculpt Multiple Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 1 and all(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        selected_objects = context.selected_objects
        context.view_layer.objects.active = selected_objects[0]
        
        # Store original object data as a custom property on the active object
        original_data = []
        for obj in selected_objects:
            # Store material names and face indices
            materials = [mat.name for mat in obj.material_slots]
            face_materials = [face.material_index for face in obj.data.polygons]

            # Store vertex groups and modifiers
            vertex_groups = [group.name for group in obj.vertex_groups]
            modifiers = [mod.name for mod in obj.modifiers]

            # Append the stored data
            original_data.append({
                'name': obj.name,
                'materials': materials,
                'face_materials': face_materials,
                'vertex_groups': vertex_groups,
                'modifiers': modifiers,
            })
        
        # Save the data in a custom property on the active object
        context.view_layer.objects.active['original_data'] = json.dumps(original_data)

        # Join the objects for sculpting
        bpy.ops.object.join()
        bpy.ops.sculpt.sculptmode_toggle()

        return {'FINISHED'}

class MULTI_SCULPT_OT_split_objects(bpy.types.Operator):
    """Split Sculpted Objects"""
    bl_idname = "sculpt.split_objects"
    bl_label = "Split Sculpted Objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.view_layer.objects.active

        # Check if original data exists
        if 'original_data' not in active_obj:
            self.report({'ERROR'}, "Original data not found!")
            return {'CANCELLED'}

        # Get stored original data
        original_data = json.loads(active_obj['original_data'])

        # Exit sculpt mode
        bpy.ops.sculpt.sculptmode_toggle()

        # Separate objects by loose parts
        bpy.ops.mesh.separate(type='LOOSE')

        # Restore original object data (names, materials, vertex groups, modifiers)
        new_objects = context.selected_objects
        for obj, data in zip(new_objects, original_data):
            obj.name = data['name']

            # Clear existing materials and apply stored ones
            obj.data.materials.clear()
            for mat_name in data['materials']:
                mat = bpy.data.materials.get(mat_name)
                if mat:
                    obj.data.materials.append(mat)

            # Restore face material assignments
            if data['face_materials']:
                for face, mat_index in zip(obj.data.polygons, data['face_materials']):
                    face.material_index = mat_index

            # Clear and restore vertex groups
            obj.vertex_groups.clear()
            for group_name in data['vertex_groups']:
                obj.vertex_groups.new(name=group_name)

            # Clear and restore modifiers
            obj.modifiers.clear()
            for mod_name in data['modifiers']:
                mod = obj.modifiers.new(name=mod_name, type='SUBSURF')  # Add generic type, adjust as needed

        return {'FINISHED'}

class MULTI_SCULPT_PT_panel(bpy.types.Panel):
    """Creates a Panel in the N-Panel under AJO category"""
    bl_label = "Multi-Object Sculpting"
    bl_idname = "SCULPT_PT_multi_sculpt"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AJO'  # Custom category name "AJO"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("sculpt.multi_sculpt", text="Merge & Sculpt")
        layout.operator("sculpt.split_objects", text="Unmerge & Split")


def register():
    bpy.utils.register_class(MULTI_SCULPT_OT_sculpt_objects)
    bpy.utils.register_class(MULTI_SCULPT_OT_split_objects)
    bpy.utils.register_class(MULTI_SCULPT_PT_panel)

def unregister():
    bpy.utils.unregister_class(MULTI_SCULPT_OT_sculpt_objects)
    bpy.utils.unregister_class(MULTI_SCULPT_OT_split_objects)
    bpy.utils.unregister_class(MULTI_SCULPT_PT_panel)

if __name__ == "__main__":
    register()
