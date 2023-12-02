import bpy

class OT_color_attribute(bpy.types.Operator):
    bl_idname = "paint.add_color_attribute"
    bl_label = "Add Color Attribute"
    bl_description = "Adds a color attribute with the specified RGBA values and removes all existing ones"

    @classmethod
    def poll(module, context):
        return context.active_object is not None and (
            context.active_object.mode in ['OBJECT', 'VERTEX_PAINT']
        )

    def execute(self, context):
        obj = context.active_object

        if obj.type != 'MESH':
            self.report({'WARNING'}, "Object must be a mesh!")
            return {'CANCELLED'}

        mytool = context.scene.my_tool
        r, g, b, a = mytool.vp_r, mytool.vp_g, mytool.vp_b, mytool.vp_a
        
        # Correct the color values for 'BYTE_COLOR' which expects values in 0-255 range
        # r_byte, g_byte, b_byte, a_byte = int(r*255), int(g*255), int(b*255), int(a*255)

        # Remove all existing color attributes
        color_attributes = [attr for attr in obj.data.attributes if attr.domain == 'CORNER' and attr.data_type == 'BYTE_COLOR']
        for attr in color_attributes:
            obj.data.attributes.remove(attr)

        # Create a new color attribute
        bpy.ops.geometry.color_attribute_add(
            name="COLOR", 
            domain='CORNER', 
            data_type='BYTE_COLOR', 
            color=(r, g, b, a)
        )

        return {'FINISHED'}


classes = (
    OT_color_attribute,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)