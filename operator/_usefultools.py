import bpy
import subprocess
import bmesh



class Tools_VisualizeTransparentMaterial(bpy.types.Operator):
    bl_idname = "my.visualize_transparent_material"
    bl_label = "투명 MMDShader 머티리얼 가시화"
    bl_description = "Alpha=0 인 MMD Shader 머티리얼의 알파 값을 1로 변경합니다"
    
    def execute(self, context):
        # Counter for the number of materials modified
        count = 0
        
        for material in bpy.data.materials:
            if material.use_nodes and "mmd_shader" in material.node_tree.nodes:
                mmd_node = material.node_tree.nodes["mmd_shader"]
                # Check if the 'mmd_shader' has enough inputs and the alpha is not already 1
                if len(mmd_node.inputs) > 12 and mmd_node.inputs[12].default_value != 1.0:
                    mmd_node.inputs[12].default_value = 1.0
                    count += 1
                        
        if count > 0:
            self.report({'INFO'}, f"{count}개의 투명 머티리얼 가시화 완료")
        else:
            self.report({'INFO'}, "투명 머티리얼이 없습니다.")
        
        return {'FINISHED'}



def remove_shape_keys(obj):
    while obj.data.shape_keys:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.shape_key_remove(all=True)

def count_triangles(ob):
    if ob.type != "MESH":
        return 0
    return sum(1 for polygon in ob.data.polygons if len(polygon.vertices) == 3)

def count_vertexes(ob):
    if ob.type != "MESH":
        return 0
    return len(ob.data.vertices)

class Decimate(bpy.types.Operator):
    bl_idname = "my.apply_decimate"
    bl_label = "Apply Decimate"

    @classmethod
    def poll(module, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        my_tool = context.scene.my_tool
        decimate_ratio = my_tool.decimate_ratio
        
        remove_shape_keys(obj)

        # Using bmesh to convert to triangles
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(obj.data)
        bm.free()

        # Apply Decimate Modifier
        mod = obj.modifiers.new(name="Decimate", type='DECIMATE')
        mod.ratio = decimate_ratio
        bpy.ops.object.modifier_apply(modifier=mod.name)

        return {'FINISHED'}


class Solidify(bpy.types.Operator):
    bl_idname = "my.apply_solidify"
    bl_label = "솔리디파이"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        my_tool = context.scene.my_tool
        
        try:
            # 모디파이어를 추가하고 설정
            mod = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
            mod.thickness = my_tool.solidify_thickness
            
            # 모디파이어 적용
            bpy.ops.object.modifier_apply({'object': obj}, modifier=mod.name)
        except Exception as e:
            # 에러가 발생하면 콘솔에 출력
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}


class TRANSFER_OT_properties(bpy.types.Operator):
    bl_idname = "transfer.properties"
    bl_label = "속성 전송"
    bl_description = "3DMigoto 속성을 대상 오브젝트로 전송"

    def execute(self, context):
        my_tool = context.scene.my_tool
        
        base_obj = my_tool.base_object
        target_obj = my_tool.target_object
        
        if not base_obj or not target_obj:
            self.report({'ERROR'}, "Both Base and Target objects must be set!")
            return {'CANCELLED'}
        
        # 속성 전송
        properties_to_transfer = [
            "3DMigoto:FirstIndex", "3DMigoto:FirstVertex", "3DMigoto:IBFormat",
            "3DMigoto:TEXCOORD.xy", "3DMigoto:VBLayout", "3DMigoto:VBStride"
        ]
        
        for prop in properties_to_transfer:
            if prop in base_obj:
                target_obj[prop] = base_obj[prop]

        self.report({'INFO'}, "속성 전송 완료")

        return {'FINISHED'}



classes = (
    Tools_VisualizeTransparentMaterial,
    Decimate,
    Solidify,
    TRANSFER_OT_properties,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)