import bpy
from . import addon_updater_ops
from ._utils import show_info_message

class MainPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Genshin Mod Tools"
    #bl_options = {"DEFAULT_CLOSED"}




class FinalCheck(MainPanel, bpy.types.Panel):
    bl_idname = "FINAL_PT_gmt"
    bl_label = "Final Check"

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="INFO")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        displayed_any = False

        from .operator._finalcheck import (
            extract_character_name, 
            characters, 
            check_custom_properties, 
            check_vertex_groups, 
            check_uv_maps,
            check_color_attributes,
        )

        if mytool.set_advanced_settings:
            layout.prop(mytool, "show_compare_vertex_centers")
        if mytool.show_compare_vertex_centers:
            layout.prop(mytool, "finalcheck_threshold", text="거리 민감도")
            layout.prop(mytool, "finalcheck_weight_threshold", text="웨이트 민감도")
            layout.operator("object.compare_vertex_centers", text="Run")

        enable_final_check = mytool.enable_final_check
        if not enable_final_check:
            return None
        
        for obj in scene.objects:
            if obj.type == 'MESH':
                character_name = extract_character_name(obj.name)
                if not character_name or character_name not in characters:
                    continue

                missing_props = check_custom_properties(obj)
                vg_warning = check_vertex_groups(obj)
                uv_warnings = check_uv_maps(obj)
                color_warnings = check_color_attributes(obj)

                vg_discrepancies = obj.get('vertex_group_discrepancies', [])

                if missing_props or vg_warning or uv_warnings or vg_discrepancies or color_warnings:
                    displayed_any = True
                    box = layout.box()
                    box.label(text=obj.name, icon='MESH_DATA')

                    if missing_props:
                        prop_box = box.box()
                        prop_box.label(text="커스텀 속성", icon='MODIFIER')
                        for prop in missing_props:
                            prop_box.label(text=f"누락됨: {prop}", icon='ERROR')

                    if vg_warning or vg_discrepancies:
                        vg_box = box.box()
                        vg_box.label(text="버텍스 그룹", icon='GROUP_VERTEX')
                        for warning in vg_warning:
                            vg_box.label(text=warning, icon='ERROR')
                        for discrepancy in vg_discrepancies:
                            vg_box.label(text=f"중심점 차이: {discrepancy}", icon='ERROR')

                    if uv_warnings:
                        uv_box = box.box()
                        uv_box.label(text="UV 맵", icon='GROUP_UVS')
                        for warning in uv_warnings:
                            uv_box.label(text=warning, icon='ERROR')

                    if color_warnings:
                        color_box = box.box()
                        color_box.label(text="색상 속성", icon='VPAINT_HLT')
                        for warning in color_warnings:
                            color_box.label(text=warning, icon='ERROR')

        if not displayed_any:
            return None    

class Import_Export(MainPanel, bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_idname = "FILE_PT_Imexport"
    bl_label = "Import and Export"
    bl_options = {"DEFAULT_CLOSED"}

    from blender_3dmigoto_gimi import Import3DMigotoFrameAnalysis, Import3DMigotoRaw

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="PACKAGE")

    def draw(self, context):
        my_tool = context.scene.my_tool
        layout = self.layout

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(my_tool, 'iae_mode', expand=True)

        if my_tool.iae_mode == 'IMPORT':

            import_box = layout.box()
            try:
                from mmd_tools.operators.fileio import ImportPmx
                import_box.label(text="덤프, vb-ib, pmx")
                import_split = import_box.split(factor=1/3)
                import_split.operator("import_mesh.migoto_frame_analysis", text="Dump")
                import_split.operator("import_mesh.migoto_raw_buffers", text="vb,ib")
                import_split.operator("mmd_tools.import_model", text="pmx")
            except ImportError:
                import_box.label(text="덤프, vb-ib")
                import_split = import_box.split(factor=1/2)
                import_split.operator("import_mesh.migoto_frame_analysis", text="Dump")
                import_split.operator("import_mesh.migoto_raw_buffers", text="vb,ib")

            base_body = layout.box()
            base_body.label(text="zeroruka 베이스 바디")
            col = base_body.column(align=True)
            row = col.row(align=True)
            row.prop(my_tool, 'base_body_type', expand=True)
            base_body.prop(my_tool, 'bb_char', text="")
            base_body.prop(my_tool, 'import_bb_bone', text="Import with Armature")
            base_body.operator("import.basebody", text="Import Base Body")

        elif my_tool.iae_mode == 'EXPORT':

            export_box = layout.box()
            export_box.label(text="Default Export")
            export_box.operator("export_mesh_genshin.migoto", text="Export")

            joinmeshes_box = layout.box()
            joinmeshes_box.label(text="JoinMeshes by leotorrez")
            col = joinmeshes_box.column(heading="각 파츠를 분류한 콜렉션을 지정")
            col.prop(context.scene, "Head", text='Head', text_ctxt='Head', translate=False)
            col.prop(context.scene, "Body", text='Body', text_ctxt='Body', translate=False)
            col.prop(context.scene, "Dress", text='Dress', text_ctxt='Dress', translate=False)
            col.prop(context.scene, "Extra", text='Extra', text_ctxt='Extra', translate=False)

            # 경로 선택
            joinmeshes_box.label(icon="FILE_FOLDER", text="내보낼 경로 지정")
            split_1 = joinmeshes_box.split(factor=0.75)
            col_1 = split_1.column()
            col_2 = split_1.column()
            col_1.prop(my_tool, "ExportFile", text="")
            col_2.operator("export.selector", icon="FILE_FOLDER", text="")

            joinmeshes_box.separator()

            # export
            split_2 = joinmeshes_box.split()
            split_2.operator("my.execute_auxclass", text="Export Mod")
            split_2.operator("my.exportanimation", text="Export animation")

class VertexWeightsPanel(MainPanel, bpy.types.Panel):
    bl_label = "Vertex Weights"
    bl_idname = "VW_PT_VertexWeightsPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="WPAINT_HLT")

    def draw(self, context):
        layout = self.layout
        mytool = context.scene.my_tool

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(mytool, 'vg_mode', expand=True)
        box.prop(mytool, "source_object", text="Source Object")
        box.prop(mytool, "destination_object", text="Destination Object")

        if mytool.vg_mode == 'MANUAL':
            manual_box = layout.box()
            manual_box.label(text="Manual", icon='MOD_VERTEX_WEIGHT')
            manual_box.prop(mytool, "num_closest_groups")
            manual_box.prop(mytool, "font_size")
            manual_box.prop(mytool, "quick_mapping")
            if mytool.quick_mapping:
                manual_box.prop(mytool, "quick_mapping_merge_vg")
            from .tools.vg_manual import drawing_started
            if not drawing_started:
                manual_box.operator("vertex.draw_closest_vertex_groups", text="Start")
            else:
                if mytool.quick_mapping:
                    manual_box.label(text="[Quick Mapping 작동중]")
                    manual_box.label(text="Quick Mapping 모드에서는")
                    manual_box.label(text="마우스 우 클릭시 종료됩니다.")
                else:
                    manual_box.operator("vertex.stop_drawing_vertex_groups", text="Stop")


        elif mytool.vg_mode == 'REMAP':
            remap_box = layout.box()
            remap_box.label(text="Select VG Remap Version", icon='MOD_VERTEX_WEIGHT')
            remap_box.prop(mytool, "remap_version", text="Version")

            if mytool.remap_version == 'version1':
                remap_box.prop(mytool, "advanced_settings", text="Advanced Settings")
                
                if mytool.advanced_settings:
                    remap_box.label(text="Distance Mode", icon='ARROW_LEFTRIGHT')
                    remap_box.prop(mytool, "distance_mode", text="Mode")
                    remap_box.prop(mytool, "post_processing", text="Anti-Aliasing")

            if mytool.remap_version == 'version2':
                if mytool.reference_destination:
                    
                    remap_box.prop(mytool, "REF_DEST_BOX", text="레퍼런스 지정")
                    if mytool.REF_DEST_BOX:
                        remap_box.prop(mytool, "REF_DEST", text="Reference Destination")

                remap_box.prop(mytool, "weighted", text="Weighted")
                remap_box.prop(mytool, "MERGE_VG", text="Merge VG after Remap")

            if mytool.remap_version == 'version3':
                if mytool.reference_destination:
                    remap_box.prop(mytool, "REF_DEST_BOX", text="레퍼런스 지정")
                    if mytool.REF_DEST_BOX:
                        remap_box.prop(mytool, "REF_DEST", text="Reference Destination")
                    remap_box.prop(mytool, "skip_numeric_vg", text="따로 지정한 버텍스 그룹의 매핑 제외")
                    
                    if mytool.skip_numeric_vg:
                        remap_box.prop(mytool, "custom_remap", text="커스텀 리맵")

                        if mytool.custom_remap:
                            custom_remap_specific_box = remap_box.box()
                            custom_remap_specific_box.label(text="Custom Remap Settings", icon='MOD_VERTEX_WEIGHT')
                            custom_remap_specific_box.prop(mytool, "character_name", text="캐릭터 선택")

                            row = custom_remap_specific_box.row(align=True)
                            row.operator("simple.open_ini", text="Open INI File")

                remap_box.prop(mytool, "v3_advanced", text="Advanced Settings")
                if mytool.v3_advanced:
                    remap_box.prop(mytool, "TOLERANCE", text="Tolerance Range")
                    remap_box.prop(mytool, "alpha", text="Interpolation Strength")

                remap_box.prop(mytool, "weighted", text="Weighted")
                remap_box.prop(mytool, "MERGE_VG", text="Merge VG after Remap")
            remap_box.operator("my.transfer_vertex_weights", text="Transfer Weights")

        vg1_box = layout.box()
        vg1_box.label(text="Vertex Groups", icon='GROUP_VERTEX')

        vg1_box.prop(mytool, "merge_mode", text="Mode")

        if mytool.merge_mode == '1':
            vg1_box.prop(mytool, "vertex_groups", text="Vertex Groups")

        if mytool.merge_mode == '2':
            vg1_box.prop(mytool, "smallest_group_number", text="Smallest Group")
            vg1_box.prop(mytool, "largest_group_number", text="Largest Group")

        vg1_box.operator("my.merge_vertex_weights", text="Merge")
        vg1_box.operator("my.remove_unused_vertex_groups")
        vg1_box.operator("my.normalize_vertex_weights", text="Normalize All")


class color_attribute(MainPanel, bpy.types.Panel):
    bl_label = "Color Attribute"
    bl_idname = "COLOR_PT_ColorAttributePanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="VPAINT_HLT")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        merge_box = layout.box()

        merge_box.label(text="Color Attributes 설정", icon="GROUP_VCOL")
        if bpy.app.version < (2, 93, 0):
            merge_box.label(text="경고: 블렌더 2.93 이하 버전에서는 정상 작동하지 않을 수 있습니다.", icon="ERROR")

        merge_box.prop(mytool, "vp_r", text="Red")
        merge_box.prop(mytool, "vp_g", text="Green")
        merge_box.prop(mytool, "vp_b", text="Blue")
        merge_box.prop(mytool, "vp_a", text="Alpha")

        merge_box.operator("paint.add_color_attribute", text="Set Color")

class UVMapPanel(MainPanel, bpy.types.Panel):
    bl_label = "UV Map"
    bl_idname = "UVMAP_PT_UVMapPanel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="UV")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        merge_box = layout.box()
        merge_box.label(icon="FILE_FOLDER", text="텍스쳐를 저장할 경로 지정")
        row = merge_box.row()
        row.prop(mytool, "output_filepath", text="")

        if mytool.set_advanced_settings:
            merge_box.prop(mytool, "skip_matcap", text="Skip Sphere Texture")
            merge_box.prop(mytool, "skip_toon_texture", text="Skip Toon Texture")
        merge_box.prop(mytool, "full_auto_uvmap", text="Full Auto")
        merge_box.prop(mytool, "alpha_invert", text="Invert Alpha Channel")
        merge_box.prop(mytool, "link_materials", text="Link Materials")
        
        #size_box = merge_box.box()
        #size_box.prop(mytool, "texture_size_mode", text="Texture Size Mode")
        # merge_box.prop(mytool, "max_texture_size")
        if mytool.max_texture_mode == 'each':
            merge_box.prop(mytool, "max_texture_size", text="Max Texure Size(px)")
        elif mytool.max_texture_mode == 'atlas':
            merge_box.prop(mytool, "max_texture_size", text="Max Atlas Size(px)")
        
        mode_box = merge_box.box()
        mode_box.label(text="Select Mode")
        max_texture_mode = mode_box.split(factor=0.5)
        if mytool.uv_mapping_mode == "rectpack":
            max_texture_mode.label(text="Sizing Mode")
            max_texture_mode.prop(mytool, "max_texture_mode", text="")
        if mytool.set_advanced_settings:
            packing_mode = mode_box.split(factor=0.5)
            packing_mode.label(text="Packing Mode")
            packing_mode.prop(mytool, "uv_mapping_mode", text="")

        #if mytool.uv_mapping_mode == 'rectpack':
        #    mode_box.prop(mytool, "bin_algo", text="Bin Algorithm")
        #    mode_box.prop(mytool, "pack_algo", text="Pack Algorithm")
        #    mode_box.prop(mytool, "sort_algo", text="Sort Algorithm")
        #    mode_box.prop(mytool, "uvmap_rotation", text="Rotation")

        merge_box.operator("start.autouvmap", text="UV Mapping")

class UsefulToolsPanel(MainPanel, bpy.types.Panel):
    bl_label = "Tools"
    bl_idname = "TOOLS_PT_Tools_UsefulTools"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="TOOL_SETTINGS")
    
    def draw(self, context):
        layout = self.layout
        my_tool = context.scene.my_tool
        obj = context.active_object

        tool_box = layout.box()
        tool_box.label(text="툴", icon='TOOL_SETTINGS')
        tool_box.operator("my.visualize_transparent_material", text="MMDShader 가시화")

        deci_box = layout.box()
        deci_box.label(text="데시메이트", icon='MOD_DECIM')

        if obj and obj.type == 'MESH':
            from .operator._usefultools import count_triangles, count_vertexes
            tri_count = count_triangles(obj)
            vert_count = count_vertexes(obj)
            
            split_info = deci_box.split(factor=0.5)
            split_info.label(text=f"삼각폴리곤 개수: {tri_count}")
            split_info.label(text=f"버텍스 개수: {vert_count}")

        split = deci_box.split(factor=0.7)
        split.prop(my_tool, "decimate_ratio", text="비율")
        split.operator("my.apply_decimate", text="적용")

        solidify_box = layout.box()
        solidify_box.label(text="솔리디파이", icon='MOD_SOLIDIFY')
        solidify_split = solidify_box.split(factor=0.7)
        solidify_split.prop(my_tool, "solidify_thickness", text="두께")
        solidify_split.operator("my.apply_solidify", text="적용")

        transfer_box = layout.box()
        transfer_box.label(text="3DMigoto 속성 전송")
        transfer_box.prop(my_tool, "target_object", text="Target Object")
        transfer_box.prop(my_tool, "base_object", text="Base Object")
        
        transfer_box.operator("transfer.properties")

class UpdateMenu(MainPanel, bpy.types.Panel):
    bl_label = 'Updates'
    bl_idname = 'BGMT_PT_Update_Menu'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="URL")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        tool = context.scene.my_tool

        addon_updater_ops.update_settings_ui(self, context)

        try:
            from bgmt import PackageStatus
        except ModuleNotFoundError:
            from blender_genshin_mod_tools import PackageStatus
        status = PackageStatus.get_instance()
        package_list_str = ", ".join(status.packages)
        module_box = layout.box()
        module_box.label(text="모듈 설치 여부")
        if status.installed_packages:
            module_box.label(text=f"{package_list_str}: 설치됨")
        else:
            module_box.label(text="설치되지 않음")
            module_box.operator("start.install_modules", text="설치")


class Settings(MainPanel, bpy.types.Panel):
    bl_label = 'Settings'
    bl_idname = 'UI_PT_Settings'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="SETTINGS")

    def draw(self, context):
        layout = self.layout
        mytool = context.scene.my_tool
        prefs = context.preferences.addons[__package__].preferences

        merge_box = layout.box()
        merge_box.prop(mytool, "set_advanced_settings", text="고급 설정 사용")
        merge_box.prop(mytool, "enable_final_check", text="Final Check 활성화")

        path_box = layout.box()
        path_box.label(text="경로 지정")
        bb_col = path_box.column(heading="zeroruka 베이스 바디")
        bb_col.prop(prefs, "basebody_file_path", text="")

        credits_box = layout.box()
        split_leo = credits_box.split(factor=0.8)
        split_leo.label(text="leotorrez - Export/JoinMeshes")
        split_leo.operator('smc.browser', text='Github').link = 'https://github.com/leotorrez/LeoTools/blob/main/JoinMeshes.py'

        split_sns = credits_box.split(factor=0.8)
        split_sns.label(text="SilentNightSound - VG Groups, VG Remap v1")
        split_sns.operator('smc.browser', text='Github').link = 'https://github.com/SilentNightSound/GI-Model-Importer/tree/main/Tools'

        split_kk = credits_box.split(factor=0.8)
        split_kk.label(text="kusaknee - VG Remap v2")
        split_kk.operator('smc.browser', text='Github').link = 'https://github.com/kusaknee/gimi_scripts/blob/master/vg_remap.py'

    
    


classes = (
    FinalCheck,
    Import_Export,
    UVMapPanel,
    VertexWeightsPanel,
    color_attribute,
    UsefulToolsPanel,
    UpdateMenu,
    Settings,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)