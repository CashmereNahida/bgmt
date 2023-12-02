import bpy
try:
    from blender_genshin_mod_tools import PackageStatus
except ModuleNotFoundError:
    from blender_genshin_mod_tools_001 import PackageStatus
from .._utils import show_info_message

def update_max_texture_size(self, context):
    my_tool = context.scene.my_tool
    if my_tool.max_texture_mode == 'atlas':
        my_tool.max_texture_size = (self.max_texture_size // 1024) * 1024

class OT_UVMAP(bpy.types.Operator):
    bl_idname = "start.autouvmap"
    bl_label = "UV Mapping"
    bl_description = "선택된 메쉬들의 텍스쳐를 패킹하고 UV 맵을 업데이트 합니다."

    def execute(self, context):
        status = PackageStatus.get_instance()

        if not status.installed_packages:
            show_info_message("필요한 라이브러리가 설치되어 있지 않아 텍스쳐 패킹을 시도할 수 없습니다.")
            return {'CANCELLED'}

        scene = context.scene
        mytool = scene.my_tool

        if not mytool.set_advanced_settings:
            mytool.uv_mapping_mode = "rectpack"

        #try:
        if mytool.uv_mapping_mode == "simple":
            from ..tools.uvmapv2 import uv_map_merge
            uv_map_merge(mytool.max_texture_size, mytool.output_filepath, mytool.skip_matcap, mytool.skip_toon_texture, mytool.full_auto_uvmap, mytool.alpha_invert)
        
        elif mytool.uv_mapping_mode == "rectpack":
            from ..tools.uvmapv3 import uv_map_merge
            uv_map_merge(mytool.output_filepath, mytool.skip_matcap, mytool.skip_toon_texture, mytool.full_auto_uvmap, mytool.alpha_invert, mytool.max_texture_size, mytool.link_materials, mytool.max_texture_mode)

        #except Exception as e:
            #show_info_message(f"텍스쳐 패킹 및 UV 맵 업데이트 중 오류 발생: {e}")
            #return {'CANCELLED'}

        return {'FINISHED'}


classes = (
    OT_UVMAP,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)