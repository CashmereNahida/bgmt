import traceback
import bpy
import os
import json
import re

from bpy_extras.view3d_utils import location_3d_to_region_2d
from math import cos, sin
from mathutils import Vector




characters = {
    "Albedo": 93,
    "Alhaitham": 127,
    "Aloy": 101,
    "Amber": 77,
    "AmberCN": 77,
    "Ayaka": 117,
    "Ayato": 119,
    "Baizhu": 118,
    "Barbara": 102,
    "BarbaraSummertime": 86,
    "Beidou": 122,
    "Bennett": 79,
    "Candace": 125,
    "Charlotte": 102,
    "Childe": 73,
    "Chongyun": 76,
    "Collei": 108,
    "Cyno": 118,
    "Dehya": 113,
    "Diluc": 85,
    "DilucFlamme": 126,
    "Diona": 80,
    "Dori": 106,
    "Eula": 109,
    "Faruzan": 121,
    "Fischl": 94,
    "FischlHighness": 89,
    "Freminet": 103,
    "Furina": 110,
    "FurinaPonytail": 8,
    "Ganyu": 92,
    "Gorou": 79,
    "Heizou": 109,
    "HuTao": 118,
    "Itto": 123,
    "Jean": 104,
    "JeanCN": 104,
    "JeanSea": 84,
    "Kaeya": 86,
    "Kaveh": 114,
    "Kazuha": 101,
    "Keqing": 109,
    "KeqingOpulent": 102,
    "Kirara": 121,
    "Klee": 93,
    "KleeBlossomingStarlight": 91,
    "Kokomi": 123,
    "KujouSara": 117,
    "Layla": 114,
    "Lisa": 103,
    "LisaStudent": 98,
    "Lynette": 113,
    "Lyney": 102,
    "Mika": 102,
    "Mona": 106,
    "MonaCN": 106,
    "Nahida": 110,
    "Neuvillette": 115,
    "Nilou": 134,
    "Ningguang": 118,
    "NingguangOrchid": 114,
    "Noelle": 108,
    "Qiqi": 102,
    "Raiden": 117,
    "RaidenShogun": 117,
    "Razor": 110,
    "Rosaria": 97,
    "RosariaCN": 97,
    "Sayu": 93,
    "Shenhe": 109,
    "Shinobu": 101,
    "Sucrose": 106,
    "Thoma": 89,
    "Tighnari": 101,
    "TravelerBoy": 90,
    "TravelerGirl": 113,
    "Venti": 116,
    "Wanderer": 102,
    "Wriothesley": 64,
    "Xiangling": 76,
    "Xiao": 95,
    "Xingqiu": 91,
    "Xinyan": 86,
    "Yae": 125,
    "Yanfei": 100,
    "YaoYao": 111,
    "Yelan": 112,
    "Yoimiya": 103,
    "Yunjin": 128,
    "Zhongli": 97,
}



mesh_name_pattern = re.compile(r"^(.+?)(Body|Head|Dress|Extra)", re.IGNORECASE)

def extract_character_name(mesh_name):
    match = mesh_name_pattern.match(mesh_name)
    if match:
        character_name = match.group(1)
        return character_name
    return None






def check_custom_properties(obj):
    required_props = [
        "3DMigoto:FirstIndex", "3DMigoto:FirstVertex", "3DMigoto:IBFormat",
        "3DMigoto:TEXCOORD.xy", "3DMigoto:VBLayout", "3DMigoto:VBStride"
    ]
    missing_props = [prop for prop in required_props if prop not in obj.keys()]
    return missing_props


def check_vertex_groups(obj):
    warnings = []

    if not obj.vertex_groups:
        warnings.append("버텍스 그룹이 없습니다.")
        return warnings

    match = mesh_name_pattern.match(obj.name)
    if match:
        character_name = match.group(1)
        if character_name in characters:
            max_vg_index = characters[character_name]
            expected_groups = {str(i) for i in range(max_vg_index + 1)}
            actual_groups = {group.name for group in obj.vertex_groups}

            missing_groups = expected_groups - actual_groups
            extra_groups = actual_groups - expected_groups

            if missing_groups:
                warnings.append(f"{character_name}: 누락됨 - {', '.join(sorted(missing_groups))}")
            if extra_groups:
                warnings.append(f"{character_name}: 초과됨 - {', '.join(sorted(extra_groups))}")
        else:
            warnings.append(f"{character_name}는 잘못된 이름입니다.")
    else:
        warnings.append("매쉬 이름에서 캐릭터 이름을 추출할 수 없습니다.")

    return warnings


def check_uv_maps(obj):
    uv_maps = obj.data.uv_layers
    uv_map_names = [uv.name for uv in uv_maps]

    required_uv_maps = ["TEXCOORD.xy", "TEXCOORD1.xy"]

    warnings = []

    if required_uv_maps[0] not in uv_map_names:
        warnings.append("TEXCOORD.xy가 누락됨")

    if len(uv_maps) > 2 or any(uv.name not in required_uv_maps for uv in uv_maps):
        extra_uv_maps = [name for name in uv_map_names if name not in required_uv_maps]
        if extra_uv_maps:
            warnings.append("잘못된 UV Map: " + ", ".join(extra_uv_maps))

    return warnings


def check_color_attributes(obj):
    color_attributes = obj.data.vertex_colors
    color_attr_names = [color.name for color in color_attributes]

    required_color_attr_name = "COLOR"

    warnings = []

    if required_color_attr_name not in color_attr_names:
        warnings.append("색상 속성이 누락됨")

    if len(color_attributes) > 1:
        extra_color_attrs = [name for name in color_attr_names if name != required_color_attr_name]
        if extra_color_attrs:
            warnings.append(f"잘못된 색상 속성: {', '.join(extra_color_attrs)}")

    return warnings





class OBJECT_OT_CompareVertexCenters(bpy.types.Operator):
    """비교 작업을 시작합니다."""
    bl_idname = "object.compare_vertex_centers"
    bl_label = "중심점 비교"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):

        scene = context.scene
        mytool = scene.my_tool
        json_path = bpy.path.abspath('//vertex_group_centers.json')

        vg_centers_data = load_vertex_group_centers(json_path)
        
        for obj in context.visible_objects:
            if obj.type == 'MESH':
                character_name = extract_character_name(obj.name)
                if character_name in vg_centers_data:
                    discrepancies = compare_vertex_group_centers(obj, character_name, vg_centers_data, mytool.finalcheck_threshold, mytool.finalcheck_weight_threshold)

                    for discrepancy in discrepancies:
                        self.report({'WARNING'}, f"{obj.name} - 중심점 차이: {discrepancy}")

                    obj['vertex_group_discrepancies'] = discrepancies

        return {'FINISHED'}

def load_vertex_group_centers(json_path):
    if not os.path.exists(json_path):
        return {}
    
    with open(json_path, "r") as infile:
        return json.load(infile)

def compare_vertex_group_centers(obj, character_name, vg_centers_data, threshold=0.0001, weight_threshold=0.001):
    vg_centers = vg_centers_data.get(character_name, {})
    discrepancies = []
    for group in obj.vertex_groups:

        if group.weight == 0:
            continue

        group_name = group.name
        if group_name in vg_centers:
            member_vertices = [
                v for v in obj.data.vertices 
                if any(g.group == group.index and g.weight > weight_threshold for g in v.groups)
            ]
            if not member_vertices:
                continue
            center = sum((v.co for v in member_vertices), Vector()) / len(member_vertices)
            
            stored_center_data = vg_centers.get(str(group.index))
            if stored_center_data:
                stored_center = Vector((stored_center_data['x'], stored_center_data['y'], stored_center_data['z']))
                discrepancy_length = (stored_center - center).length
                if discrepancy_length > threshold:
                    discrepancies.append(group_name)
                    print(f"Group: {group.index}")
                    print(f"Stored Center: {stored_center}, Calculated Center: {center}, Discrepancy: {discrepancy_length}")
    
    return discrepancies

        



classes = (
    OBJECT_OT_CompareVertexCenters,
)


def register():

    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    
    for c in classes:
        bpy.utils.unregister_class(c)