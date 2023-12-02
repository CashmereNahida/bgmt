import bpy
import itertools




class OT_TransferVertexWeights(bpy.types.Operator):
    bl_idname = "my.transfer_vertex_weights"
    bl_label = "Transfer Vertex Weights"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if not mytool.source_object or not mytool.destination_object:
            self.report({'WARNING'}, "Please select both source and destination objects.")
            return {'CANCELLED'}

        if mytool.remap_version == 'version1':
            from ..tools.vg_remap import vgremap_v1_weights
            vgremap_v1_weights(mytool.source_object, mytool.destination_object)
        elif mytool.remap_version == 'version2':
            from ..tools.vg_remap import vgremap_v2_weights
            vgremap_v2_weights(mytool.source_object, mytool.destination_object, mytool.REF_DEST, mytool.weighted, mytool.MERGE_VG)
        elif mytool.remap_version == 'version3':
            from ..tools.vg_remap import vgremap_v3_weights
            vgremap_v3_weights(mytool.source_object, mytool.destination_object, mytool.REF_DEST, mytool.weighted, mytool.MERGE_VG, mytool.alpha, mytool.TOLERANCE, mytool.character_name, mytool.skip_numeric_vg, mytool.custom_remap, mytool.v3_advanced) #935

        return {'FINISHED'}

class Vertex_NormalizeVertexWeights(bpy.types.Operator):
    bl_idname = "my.normalize_vertex_weights"
    bl_label = "Normalize Vertex Weights"
    
    def execute(self, context):
        # Iterate over selected objects
        for obj in bpy.context.selected_objects:
            if len(obj.vertex_groups) == 0:
                self.report({'WARNING'}, f"'{obj.name}'에는 버텍스 그룹이 없습니다.")
                continue

            bpy.ops.object.vertex_group_normalize_all({'object': obj})

        return {'FINISHED'}

class OT_RemoveUnusedVertexGroups(bpy.types.Operator):
# take from: https://blenderartists.org/t/batch-delete-vertex-groups-script/449881/23#:~:text=10%20MONTHS%20LATER-,AdenFlorian,-Jun%202021
    bl_idname = "my.remove_unused_vertex_groups"
    bl_label = "사용하지 않는 버텍스 그룹 삭제"

    def execute(self, context):
        ob = context.active_object
        mytool = context.scene.my_tool
        mode = int(mytool.merge_mode)

        if ob is None:
            self.report({'WARNING'}, "선택된 오브젝트를 찾을 수 없습니다.")
            return {'CANCELLED'}

        ob.update_from_editmode()

        # Get the target vertex groups based on the mode
        vgroup_names = []
        if mode == 1:
            vgroup_names = mytool.vertex_groups.split(",")
        elif mode == 2:
            vgroup_names = [f"{i}" for i in range(mytool.smallest_group_number, mytool.largest_group_number+1)]
        elif mode == 3:
            for obj in bpy.context.selected_objects:
                vgroup_names.extend([x.name.split(".")[0] for x in obj.vertex_groups])
        else:
            self.report({'ERROR'}, "모드가 선택되지 않았습니다.")
            return {'CANCELLED'}

        vgroup_used = {i: False for i, k in enumerate(ob.vertex_groups)}

        for v in ob.data.vertices:
            for g in v.groups:
                if g.weight > 0.0 and ob.vertex_groups[g.group].name in vgroup_names:
                    vgroup_used[g.group] = True

        deleted_count = 0

        for i, used in sorted(vgroup_used.items(), reverse=True):
            if not used and ob.vertex_groups[i].name in vgroup_names:
                ob.vertex_groups.remove(ob.vertex_groups[i])
                deleted_count += 1

        if deleted_count > 0:
            self.report({'INFO'}, f"{deleted_count}개의 사용하지 않는 버텍스 그룹이 삭제되었습니다.")
        else:
            self.report({'INFO'}, "사용하지 않는 버텍스 그룹이 없습니다.")

        return {'FINISHED'}

class OT_MergeVertexGroups(bpy.types.Operator):
# Merge Vertex Groups by SilentNightSound#7430
# https://github.com/SilentNightSound/GI-Model-Importer/blob/main/Tools/blender_merge_vg.txt
    bl_idname = "my.merge_vertex_weights"
    bl_label = "Merge Vertex Weights"
    #bl_options = {"DEFAULT_CLOSED"}
    
    def execute(self, context):
        mytool = context.scene.my_tool
        mode = int(mytool.merge_mode)
        
        selected_obj = [obj for obj in bpy.context.selected_objects]
        vgroup_names = []

        if mode == 1:
            # Parse the vertex groups from the comma-separated property string
            vgroup_names = [mytool.vertex_groups.split(",")]
        elif mode == 2:
            vgroup_names = [[f"{i}" for i in range(mytool.smallest_group_number, mytool.largest_group_number+1)]]
        elif mode == 3:
            vgroup_names = [[x.name.split(".")[0] for x in y.vertex_groups] for y in selected_obj]
        else:
            self.report({'ERROR'}, "모드가 선택되지 않았습니다.")
            return {'CANCELLED'}

        if not vgroup_names:
            self.report({'ERROR'}, "버텍스 그룹을 찾을 수 없습니다. 오브젝트를 선택한 후 다시 시도하세요.")
            return {'CANCELLED'}

        for cur_obj, cur_vgroup in zip(selected_obj, itertools.cycle(vgroup_names)):
            if len(cur_obj.vertex_groups) == 0:
                self.report({'WARNING'}, f"'{cur_obj.name}'에는 버텍스 그룹이 없습니다.")
                continue

            for vname in cur_vgroup:
                relevant = [x.name for x in cur_obj.vertex_groups if x.name.split(".")[0] == f"{vname}"]

                if relevant:
                    vgroup = cur_obj.vertex_groups.new(name=f"x{vname}")
                        
                    for vert_id, vert in enumerate(cur_obj.data.vertices):
                        available_groups = [v_group_elem.group for v_group_elem in vert.groups]
                        
                        combined = 0
                        for v in relevant:
                            if cur_obj.vertex_groups[v].index in available_groups:
                                combined += cur_obj.vertex_groups[v].weight(vert_id)

                        if combined > 0:
                            vgroup.add([vert_id], combined ,'ADD')
                            
                    for vg in [x for x in cur_obj.vertex_groups if x.name.split(".")[0] == f"{vname}"]:
                        cur_obj.vertex_groups.remove(vg)

                    for vg in cur_obj.vertex_groups:
                        if vg.name[0].lower() == "x":
                            vg.name = vg.name[1:]
                            
            bpy.context.view_layer.objects.active = cur_obj
            bpy.ops.object.vertex_group_sort()

        return {'FINISHED'}


classes = (
    OT_TransferVertexWeights,
    Vertex_NormalizeVertexWeights,
    OT_RemoveUnusedVertexGroups,
    OT_MergeVertexGroups,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)