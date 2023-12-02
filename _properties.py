import bpy

class MyProperties(bpy.types.PropertyGroup):

    quick_mapping_merge_vg: bpy.props.BoolProperty(
        name="Merge VG",
        description="Merge VG after Quick Mapping",
        default=True,
    ) 

    quick_mapping: bpy.props.BoolProperty(
        name="Quick Mapping",
        description="Enable Quick Mapping",
        default=False,
    )

    num_closest_groups: bpy.props.IntProperty(
        name="Closest Groups",
        description="표시할 가까운 버텍스 그룹 개수",
        default=3,
        min=1,
        max=10
    )

    font_size: bpy.props.IntProperty(
        name="Font Size",
        description="뷰포트에 표시되는 버텍스 그룹 이름 폰트 사이즈",
        default=20,
        min=10,
        max=50
    )

    vg_mode: bpy.props.EnumProperty(
        name="Select Mode",
        description="선택",
        items=[
            ("MANUAL", "Manual", "수동"),
            ("REMAP", "Remap", "리맵"),
        ]
    )

    iae_mode: bpy.props.EnumProperty(
        name="Select Import or Export",
        description="선택",
        items=[
            ("IMPORT", "Import", "임포트"),
            ("EXPORT", "Export", "익스포트"),
        ]
    )

    base_body_type: bpy.props.EnumProperty(
        name="Base Body Type",
        description="선택",
        items=[
            ("LOLI", "Loli", "누오오오옹ㅋㅋㅋ"),
            ("TEEN", "Teen", "잼순이"),
            ("ADULT", "Adult", "닭장이잔아.."),
        ],
        default="TEEN"
    )

    from .operator._import_export import get_character_items
    bb_char: bpy.props.EnumProperty(
        name="Select Character",
        description="선택된 캐릭터에 따라 버텍스 그룹을 설정",
        items=get_character_items,
    )

    import_bb_bone: bpy.props.BoolProperty(
        name="Import with Armature",
        description="아마추어도 불러옴",
        default=False,
    )

    set_advanced_settings: bpy.props.BoolProperty(
        name="Advanced Settings",
        description="고급 설정",
        default=False,
    )

    ExportFile: bpy.props.StringProperty(
        name="ExportFile",
        description="Export File:",
        default="",
        maxlen=1024,
        )
    use_foldername : bpy.props.BoolProperty(
        name="Use foldername when exporting",
        description="Sets the export name equal to the foldername you are exporting to. Keep true unless you have changed the names",
        default=True,
    )

    ignore_hidden : bpy.props.BoolProperty(
        name="Ignore hidden objects",
        description="Does not use objects in the Blender window that are hidden while exporting mods",
        default=False,
    )

    only_selected : bpy.props.BoolProperty(
        name="Only export selected",
        description="Uses only the selected objects when deciding which meshes to export",
        default=False,
    )

    no_ramps : bpy.props.BoolProperty(
        name="Ignore shadow ramps/metal maps/diffuse guide",
        description="Skips exporting shadow ramps, metal maps and diffuse guides",
        default=True,
    )

    delete_intermediate : bpy.props.BoolProperty(
        name="Delete intermediate files",
        description="Deletes the intermediate vb/ib files after a successful export to reduce clutter",
        default=True,
    )

    credit : bpy.props.StringProperty(
        name="Credit",
        description="Name that pops up on screen when mod is loaded. If left blank, will result in no pop up",
        default='',
    )

    outline_optimization : bpy.props.BoolProperty(
        name="Outline Optimization",
        description="Recalculate outlines. Recommended for final export. Check more options below to improve quality",
        default=False,
    )
    
    toggle_rounding_outline : bpy.props.BoolProperty(
        name="Round vertex positions",
        description="Rounding of vertex positions to specify which are the overlapping vertices",
        default=True,
    ) 
    
    decimal_rounding_outline : bpy.props.IntProperty(
        name="Decimals:",
        description="Rounding of vertex positions to specify which are the overlapping vertices",
        default=3,
    )

    angle_weighted : bpy.props.BoolProperty(
        name="Weight by angle",
        description="Calculate angles to improve accuracy of outlines",
        default=False,
    )

    overlapping_faces : bpy.props.BoolProperty(
        name="Ignore overlapping faces",
        description="Detect and ignore overlapping faces to avoid buggy outlines. Recommended if you have overlaps",
        default=False,
    )

    detect_edges : bpy.props.BoolProperty(
        name="Calculate edges",
        description="Calculate for disconnected edges when rounding, closing holes in the edge outline. Slow",
        default=False,
    )

    calculate_all_faces : bpy.props.BoolProperty(
        name="Calculate outline for all faces",
        description="If you have any flat shaded internal faces or if you just need to fix outline for all faces, turn on this option for better outlines. Slow",
        default=False,
    )

    nearest_edge_distance : bpy.props.FloatProperty(
        name="Distance:",
        description="Expand grouping for edge vertices within this radial distance to close holes in the edge outline. Requires rounding",
        default=0.001,
        soft_min=0,
        precision=4,
    )

    # For the Vertex Weights section
    merge_mode: bpy.props.EnumProperty(
        name="Mode",
        items=[("1", "comma-separated", "ex) 1, 3, 13, 36..."),
               ("2", "Range Mode", "병합할 범위를 선택하세요."),
               ("3", "ALL Groups", "모든 버텍스 그룹을 병합합니다.")],
        default="3"
    )

    vertex_groups: bpy.props.StringProperty(
        name="Vertex Groups",
        description="Comma separated vertex group indices for mode 1",
    )

    smallest_group_number: bpy.props.IntProperty(name="Smallest Group Number", min=0, max=999, default=0)
    largest_group_number: bpy.props.IntProperty(name="Largest Group Number", min=0, max=999, default=999)
    
    # Add property for Mode 1 vertex_groups
    vertex_groups: bpy.props.StringProperty(name="Vertex Groups", description="Comma separated vertex group names for Mode 1", default="")
    
    decimate_ratio: bpy.props.FloatProperty(
        name="Decimate Ratio",
        description="Ratio for decimation",
        default=0.7,
        min=0.01, max=1
    )

    solidify_thickness: bpy.props.FloatProperty(
        name="Solidify Thickness",
        description="Set the thickness for the solidify modifier",
        default=0.00001,
        min=0.0,
        precision=6,
    )

    vp_r: bpy.props.FloatProperty(name="Red", default=1.0, min=0.0, max=1.0, description="Red component", precision=3)
    vp_g: bpy.props.FloatProperty(name="Green", default=0.502, min=0.0, max=1.0, description="Green component", precision=3)
    vp_b: bpy.props.FloatProperty(name="Blue", default=0.502, min=0.0, max=1.0, description="Blue component", precision=3)
    vp_a: bpy.props.FloatProperty(name="Alpha", default=0.5, min=0.0, max=1.0, description="Alpha component", precision=1)

    target_object: bpy.props.PointerProperty(
        name="Target",
        type=bpy.types.Object,
        description="Target Object"
    )
    
    base_object: bpy.props.PointerProperty(
        name="Base",
        type=bpy.types.Object,
        description="Base Object"
    )

    source_object: bpy.props.PointerProperty(
        name="Source Object",
        type=bpy.types.Object
    )

    destination_object: bpy.props.PointerProperty(
        name="Destination Object",
        type=bpy.types.Object
    )

    distance_mode: bpy.props.EnumProperty(
        name="Distance Mode",
        description="Choose the distance calculation method",
        items=[
            ('euclidean', "Euclidean", "Euclidean Distance"),
            ('manhattan', "Manhattan", "Manhattan Distance"),
            ('cosine', "Cosine", "Cosine Similarity")
        ],
        default='euclidean',
    )

    post_processing: bpy.props.BoolProperty(
        name="Post Processing",
        description="Apply post-processing to the search results",
        default=True,
    )

    advanced_settings: bpy.props.BoolProperty(
        name="Advanced Settings",
        default=False,
    )

    from .tools.vg_remap import update_remap_version, get_remap_version_items
    remap_version: bpy.props.EnumProperty(
        name="VG Remap Version",
        description="Select VG Remap Version",
        items=get_remap_version_items,
        #update=update_remap_version,
    )

    set_advanced_settings: bpy.props.BoolProperty(
        name="Set Advanced Settings",
        description="Show advanced remap versions",
        default=False,
        #update=update_remap_version,
    )

    reference_destination: bpy.props.BoolProperty(
        name="Reference Destination",
        description="Enable/Disable Reference Destination",
        default=True
    )

    REF_DEST: bpy.props.PointerProperty(
        name="REF_DEST",
        description="Drag input for Reference Destination",
        type=bpy.types.Object
    )

    REF_DEST_BOX: bpy.props.BoolProperty(
        name="REF_DEST_BOX",
        description="챈에 설명되어 있음",
        default=False
    )

    weighted: bpy.props.BoolProperty(
        name="weighted",
        default=True
    )

    MERGE_VG: bpy.props.BoolProperty(
        name="MERGE_VG",
        default=True
    )

    v3_advanced: bpy.props.BoolProperty(
        name="Advanced Settings",
        default=False
    )

    TOLERANCE: bpy.props.FloatProperty(
        name="허용 오차 범위",
        description="특정한 부분의 매핑 정밀도를 높일 때 사용",
        default=0.1,
        min=0.0,
        max=2.0,
        precision=3
    )

    alpha: bpy.props.FloatProperty(
        name="인터폴레이션 강도",
        description="가장 가까운 버텍스 그룹의 웨이트를 인터폴레이션",
        default=0.5,
        min=0.0,
        max=1.0,
        precision=3
    )

    skip_numeric_vg: bpy.props.BoolProperty(
        name="숫자로 된 버텍스 그룹 스킵",
        description="MMD 모델에서 본인이 직접 지정한 버텍스 그룹의 매핑을 스킵하려면 이 기능을 활성화하세요",
        default=False
    )

    custom_remap: bpy.props.BoolProperty(
        name="커스텀 리맵",
        default=False
    )

    from .tools.vg_remap import get_character_names_from_ini
    character_name: bpy.props.EnumProperty(
        name="Character Name",
        description="Name of the character for vertex group remapping",
        items=get_character_names_from_ini
    )

    skip_matcap: bpy.props.BoolProperty(
        name="Skip Sphere Texture",
        default=True
    )

    skip_toon_texture: bpy.props.BoolProperty(
        name="Skip Toon Texture",
        default=True
    )

    full_auto_uvmap: bpy.props.BoolProperty(
        name="Full Auto UVMapping",
        description="동일한 매쉬 이름끼리 텍스쳐를 패킹합니다",
        default=False
    )

    alpha_invert: bpy.props.BoolProperty(
        name="알파 반전",
        description="설정할 시 텍스쳐를 알파 반전후 저장합니다",
        default=False
    )

    link_materials: bpy.props.BoolProperty(
        name="Link Materials",
        description="텍스쳐 패킹 후 패킹된 텍스쳐로 매쉬의 매테리얼을 업데이트합니다",
        default=True
    )

    from .operator._uvmap import update_max_texture_size
    max_texture_size: bpy.props.IntProperty(
        name="Max Texture Size",
        description="Maximum size of each side of the combined texture",
        default=1024,
        update=update_max_texture_size
    )

    max_texture_mode: bpy.props.EnumProperty(
        name="Sizing Mode",
        description="사이즈 조절 모드를 선택",
        items=[
            ('each', 'Each', '개별 텍스쳐 크기를 제한한 후 패킹합니다.'),
            #('atlas', 'Atlas', '최종 텍스쳐 크기를 지정하고 개별 텍스쳐 크기를 자동으로 조절합니다.'),
        ],
        default='each',
    )

    output_filepath: bpy.props.StringProperty(
        name="Output Filepath",
        description="Filepath to save the combined texture",
        default="//combined_texture.png",
        subtype='FILE_PATH'
    )

    uv_mapping_mode: bpy.props.EnumProperty(
        name="UV Mapping Mode",
        description="Select UV Mapping mode",
        items=[
            ('simple', 'Simple', '크기와 상관없이 텍스쳐를 순차적으로 배치'),
            ('rectpack', 'rectpack', 'rectpack 을 이용하여 텍스쳐를 패킹'),
        ],
        default='rectpack'
    )

    bin_algo: bpy.props.EnumProperty(
        name="Bin Algorithm",
        description="Bin selection heuristic",
        items=[
            ('PackingBin.BNF', 'Bin Next Fit', 'If a rectangle does not fit into the current bin, close it and try next one'),
            ('PackingBin.BFF', 'Bin First Fit', 'Pack rectangle into the first bin it fits (without closing)'),
            ('PackingBin.BBF', 'Bin Best Fit', 'Pack rectangle into the bin that gives best fitness'),
            ('PackingBin.Global', 'PackingBin Global', 'For each bin pack the rectangle with the best fitness until it is full, then continue with next bin'),
        ],
        default='PackingBin.BBF'
    )

    pack_algo: bpy.props.EnumProperty(
        name="Pack Algorithm",
        description="One of the supported packing algorithms",
        items=[
            ('MaxRectsBl', 'MaxRectsBl Algorithm', ''),
            ('MaxRectsBssf', 'MaxRectsBssf Algorithm', ''),
            ('MaxRectsBaf', 'MaxRectsBaf Algorithm', ''),
            ('MaxRectsBlsf', 'MaxRectsBlsf Algorithm', ''),
            ('SkylineBl', 'SkylineBl Algorithm', ''),
            ('SkylineBlWm', 'SkylineBlWm Algorithm', ''),
            ('SkylineMwf', 'SkylineMwf Algorithm', ''),
            ('SkylineMwfl', 'SkylineMwfl Algorithm', ''),
            ('SkylineMwfWm', 'SkylineMwfWm Algorithm', ''),
            ('SkylineMwflWm', 'SkylineMwflWm Algorithm', ''),
            ('GuillotineBssfSas', 'GuillotineBssfSas Algorithm', ''),
            ('GuillotineBssfLas', 'GuillotineBssfLas Algorithm', ''),
            ('GuillotineBssfSlas', 'GuillotineBssfSlas Algorithm', ''),
            ('GuillotineBssfLlas', 'GuillotineBssfLlas Algorithm', ''),
            ('GuillotineBssfMaxas', 'GuillotineBssfMaxas Algorithm', ''),
            ('GuillotineBssfMinas', 'GuillotineBssfMinas Algorithm', ''),
            ('GuillotineBlsfSas', 'GuillotineBlsfSas Algorithm', ''),
            ('GuillotineBlsfLas', 'GuillotineBlsfLas Algorithm', ''),
            ('GuillotineBlsfSlas', 'GuillotineBlsfSlas Algorithm', ''),
            ('GuillotineBlsfLlas', 'GuillotineBlsfLlas Algorithm', ''),
            ('GuillotineBlsfMaxas', 'GuillotineBlsfMaxas Algorithm', ''),
            ('GuillotineBlsfMinas', 'GuillotineBlsfMinas Algorithm', ''),
            ('GuillotineBafSas', 'GuillotineBafSas Algorithm', ''),
            ('GuillotineBafLas', 'GuillotineBafLas Algorithm', ''),
            ('GuillotineBafSlas', 'GuillotineBafSlas Algorithm', ''),
            ('GuillotineBafLlas', 'GuillotineBafLlas Algorithm', ''),
            ('GuillotineBafMaxas', 'GuillotineBafMaxas Algorithm', ''),
            ('GuillotineBafMinas', 'GuillotineBafMinas Algorithm', ''),
        ],
        default='MaxRectsBlsf'
    )

    sort_algo: bpy.props.EnumProperty(
        name="Sort Algorithm",
        description="Rectangle sort order before packing",
        items=[
            ('SORT_NONE', 'None', 'Rectangles left unsorted.'),
            ('SORT_AREA', 'Area', 'Sort by descending area.'),
            ('SORT_PERI', 'Perimeter', 'Sort by descending perimeter.'),
            ('SORT_DIFF', 'Difference', 'Sort by difference of rectangle sides.'),
            ('SORT_SSIDE', 'Shortest Side', 'Sort by shortest side.'),
            ('SORT_LSIDE', 'Longest Side', 'Sort by longest side.'),
            ('SORT_RATIO', 'Ratio', 'Sort by ratio between sides.'),
        ],
        default='SORT_LSIDE'
    )

    uvmap_rotation: bpy.props.BoolProperty(
        name="Enable or disable rectangle rotation",
        default=False
    )

    show_compare_vertex_centers: bpy.props.BoolProperty(
        name="(Beta)웨이트 중심점 차이 확인",
        description="원신 기본 에셋과 중심점 차이를 계산해 잘못 칠해진 정점 그룹을 검사",
        default=False,
    )

    enable_final_check: bpy.props.BoolProperty(
        name="Final Check 활성화",
        description="Final Check를 활성화 합니다",
        default=True,
    )

    finalcheck_threshold: bpy.props.FloatProperty(
        name="Compare Threshold",
        description="설정된 값 이상의 거리 차이가 나는 정점 그룹만 표시",
        default=0.001,
        min=0.000001,
        max=1.0,
        precision=6,
    )

    finalcheck_weight_threshold: bpy.props.FloatProperty(
        name="Weight Threshold",
        description="설정된 값 이하 가중치는 검사에서 제외",
        default=0.001,
        min=0.00001,
        max=0.1,
        precision=5,
    )


"""
"""
"""
"""
"""
"""
"""
"""
"""
"""

import os
from bpy_extras.io_utils import ExportHelper

class WMFileSelector(bpy.types.Operator, ExportHelper):
    """Export single mod based on current frame"""
    bl_idname = "export.selector"
    bl_label = "Destination"
    
    filename_ext = "."
    use_filter_folder = True
    # filename_ext = ".vb"
    filter_glob : bpy.props.StringProperty(
            default='.',
            options={'HIDDEN'},
            )
    use_foldername : bpy.props.BoolProperty(
        name="Use foldername when exporting",
        description="Sets the export name equal to the foldername you are exporting to. Keep true unless you have changed the names",
        default=True,
    )

    ignore_hidden : bpy.props.BoolProperty(
        name="Ignore hidden objects",
        description="Does not use objects in the Blender window that are hidden while exporting mods",
        default=True,
    )

    only_selected : bpy.props.BoolProperty(
        name="Only export selected",
        description="Uses only the selected objects when deciding which meshes to export",
        default=False,
    )

    no_ramps : bpy.props.BoolProperty(
        name="Ignore shadow ramps/metal maps/diffuse guide",
        description="Skips exporting shadow ramps, metal maps and diffuse guides",
        default=True,
    )

    delete_intermediate : bpy.props.BoolProperty(
        name="Delete intermediate files",
        description="Deletes the intermediate vb/ib files after a successful export to reduce clutter",
        default=True,
    )

    credit : bpy.props.StringProperty(
        name="Credit",
        description="Name that pops up on screen when mod is loaded. If left blank, will result in no pop up",
        default='',
    )
    outline_optimization : bpy.props.BoolProperty(
        name="Outline Optimization",
        description="Recalculate outlines. Recommended for final export. Check more options below to improve quality",
        default=False,
    )
    
    toggle_rounding_outline : bpy.props.BoolProperty(
        name="Round vertex positions",
        description="Rounding of vertex positions to specify which are the overlapping vertices",
        default=True,
    ) 
    
    decimal_rounding_outline : bpy.props.IntProperty(
        name="Decimals:",
        description="Rounding of vertex positions to specify which are the overlapping vertices",
        default=3,
    )

    angle_weighted : bpy.props.BoolProperty(
        name="Weight by angle",
        description="Calculate angles to improve accuracy of outlines",
        default=False,
    )

    overlapping_faces : bpy.props.BoolProperty(
        name="Ignore overlapping faces",
        description="Detect and ignore overlapping faces to avoid buggy outlines. Recommended if you have overlaps",
        default=False,
    )

    detect_edges : bpy.props.BoolProperty(
        name="Calculate edges",
        description="Calculate for disconnected edges when rounding, closing holes in the edge outline. Slow",
        default=False,
    )

    calculate_all_faces : bpy.props.BoolProperty(
        name="Calculate outline for all faces",
        description="If you have any flat shaded internal faces or if you just need to fix outline for all faces, turn on this option for better outlines. Slow",
        default=False,
    )

    nearest_edge_distance : bpy.props.FloatProperty(
        name="Distance:",
        description="Expand grouping for edge vertices within this radial distance to close holes in the edge outline. Requires rounding",
        default=0.001,
        soft_min=0,
        precision=4,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        
        col.prop(self, 'use_foldername')
        col.prop(self, 'ignore_hidden')
        col.prop(self, 'only_selected')
        col.prop(self, 'no_ramps')
        col.prop(self, 'delete_intermediate')
        col.prop(self, 'credit')
        layout.separator()
        
        col = layout.column(align=True)
        col.prop(self, 'outline_optimization')
        
        if self.outline_optimization:
            col.prop(self, 'toggle_rounding_outline', text='Vertex Position Rounding', toggle=True, icon="SHADING_WIRE")
            col.prop(self, 'decimal_rounding_outline')
            col.prop(self, 'angle_weighted')
            col.prop(self, 'overlapping_faces')
            if self.toggle_rounding_outline:
                col.prop(self, 'detect_edges')
            if self.detect_edges and self.toggle_rounding_outline:
                col.prop(self, 'nearest_edge_distance')
            col.prop(self, 'calculate_all_faces')

    def execute(self, context):
        userpath = self.properties.filepath
        if not os.path.isdir(userpath):
            msg = "Please select a directory not a file\n" + userpath
            self.report({'WARNING'}, msg)
        
        context.scene.my_tool.ExportFile = self.properties.filepath    
        context.scene.my_tool.use_foldername = self.properties.use_foldername
        context.scene.my_tool.ignore_hidden = self.properties.ignore_hidden
        context.scene.my_tool.only_selected = self.properties.only_selected
        context.scene.my_tool.no_ramps = self.properties.no_ramps
        context.scene.my_tool.delete_intermediate = self.properties.delete_intermediate
        context.scene.my_tool.credit = self.properties.credit

        context.scene.my_tool.outline_optimization = self.properties.outline_optimization
        context.scene.my_tool.toggle_rounding_outline = self.properties.toggle_rounding_outline
        context.scene.my_tool.decimal_rounding_outline = self.properties.decimal_rounding_outline
        context.scene.my_tool.angle_weighted = self.properties.angle_weighted
        context.scene.my_tool.overlapping_faces = self.properties.overlapping_faces
        context.scene.my_tool.detect_edges = self.properties.detect_edges
        context.scene.my_tool.calculate_all_faces = self.properties.calculate_all_faces
        context.scene.my_tool.nearest_edge_distance = self.properties.nearest_edge_distance

        return{'FINISHED'}


classes = (
    MyProperties,
    WMFileSelector,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)