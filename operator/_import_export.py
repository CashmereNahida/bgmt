import bpy
import os
import configparser
import json
import subprocess
from blender_3dmigoto_gimi import export_3dmigoto_genshin, Fatal, Import3DMigotoFrameAnalysis, import_3dmigoto

# New class for the error handling
class Fatal(Exception): pass


def show_info_message(message):
    print(message)
    message_lines = message.split('\n')
    def draw(self, context):
        for line in message_lines:
            self.layout.label(text=line)
    bpy.context.window_manager.popup_menu(draw, title="Info", icon='INFO')




        
class ImportBaseBody(bpy.types.Operator):
    bl_idname = "import.basebody"
    bl_label = "Import Base Body"

    def load_json_data(self, file_name):
        current_script_path = os.path.dirname(__file__)
        file_path = os.path.join(current_script_path, file_name)

        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        return data

    def apply_vertex_groups(self, obj, vertex_groups_data):
        obj.vertex_groups.clear()

        for v_index_str, weights in vertex_groups_data.items():
            v_index = int(v_index_str)
            for group_name, weight in weights.items():
                group = obj.vertex_groups.get(group_name)

                if group is None:
                    group = obj.vertex_groups.new(name=group_name)

                group.add([v_index], weight, 'REPLACE')

    def create_missing_vertex_groups(self, obj, vertex_group_centers):
        existing_vertex_group_names = [vg.name for vg in obj.vertex_groups]

        for vg_name, _ in vertex_group_centers.items():
            if vg_name not in existing_vertex_group_names:
                obj.vertex_groups.new(name=vg_name)

    def execute(self, context):
        from .._utils import addon_preferences
        blend_file_path = addon_preferences('basebody_file_path', '')
        
        if not blend_file_path:
            message = "파일 경로가 지정되지 않았습니다. 설정에서 zeroruka 베이스 바디 프로젝트 파일의 경로를 지정해주세요."
            show_info_message(message)
            return {'CANCELLED'}

        if not blend_file_path.endswith('.blend'):
            message = ".blend 파일이 아닙니다."
            show_info_message(message)
            return {'CANCELLED'}

        import_bone = context.scene.my_tool.import_bb_bone
        armature_name = 'Mona Armature'

        with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
            if import_bone:
                data_to.objects = [obj for obj in data_from.objects if armature_name in obj or "Base" in obj]
            else:
                data_to.objects = [obj for obj in data_from.objects if "Base" in obj]

        for obj in data_to.objects:
            bpy.context.collection.objects.link(obj)
            if obj.type == 'ARMATURE':
                if import_bone:
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                else:
                    # 아마추어 객체가 아닌 경우에만 연결합니다.
                    if "Armature" not in obj.name:
                        bpy.context.collection.objects.link(obj)

        for obj in data_to.objects:
            if obj.type == 'MESH':
                if import_bone:
                    armature_obj = bpy.data.objects.get(armature_name)
                    if not armature_obj:
                        message = f"{blend_file_path} 에서 {armature_name} 를 찾을 수 없습니다. 베이스 바디 프로젝트가 맞는지, 아마추어 이름이 Mona Armature 가 맞는지 확인하세요."
                        show_info_message(message)
                        continue
                    if obj.parent != armature_obj:
                        obj.parent = armature_obj
                        obj.matrix_parent_inverse = armature_obj.matrix_world.inverted()

        basebody_vg_data = self.load_json_data('basebody_vg_data.json')
        vertex_group_centers = self.load_json_data('vertex_group_centers.json')

        global name_mapping
        name_mapping = {
            'AMBERCN': 'AmberCN',
            'BARBARAALT': 'BarbaraSummertime',
            'FISCHLALT': 'FischlHighness',
            'HUTAO': 'HuTao',
            'JEANCN': 'JeanCN',
            'JEANSEA': 'JeanSea',
            'KEQINGOPULENT': 'KeqingOpulent',
            'KLEEALT': 'KleeBlossomingStarlight',
            'MONA': 'Mona',
            'KUJOUSARA': 'KujouSara',
            'LISAALT': 'LisaStudent',
            'MONACN': 'MonaCN',
            'NINGGUANGALT': 'NingguangOrchid',
            'RAIDEN': 'RaidenShogun',
            'ROSARIACN': 'RosariaCN',
            'LUMINE': 'TravelerGirl',
            'YAOYAO': 'YaoYao',
            'YUNJIN': 'YunJin',}

        if 'my_tool' in context.scene:
            my_tool = context.scene.my_tool
            bb_char = my_tool.bb_char

            bb_char_upper = bb_char.upper()

            if bb_char_upper in basebody_vg_data:
                for obj in data_to.objects:
                    if obj.type == 'MESH' and "Base" in obj.name:
                        self.apply_vertex_groups(obj, basebody_vg_data[bb_char_upper])
            else:
                print(f"Warning: Character '{bb_char_upper}' not found in vertex group data.")

            bb_char_mapped = name_mapping.get(bb_char, bb_char.capitalize())

            for obj in data_to.objects:
                if obj.type == 'MESH' and "Base" in obj.name:
                    self.create_missing_vertex_groups(obj, vertex_group_centers.get(bb_char_mapped, {}))
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.vertex_group_sort(sort_type='NAME')

        if 'my_tool' in context.scene:
            my_tool = context.scene.my_tool
            if my_tool.base_body_type == 'LOLI':
                self.set_shape_key_value(obj, 'Loli', 1.0)
            elif my_tool.base_body_type == 'ADULT':
                self.set_shape_key_value(obj, 'Adult', 1.0)

        return {'FINISHED'}

    def set_shape_key_value(self, mesh_object, shape_key_name, value):
        if mesh_object.data.shape_keys:
            key_blocks = mesh_object.data.shape_keys.key_blocks
            if shape_key_name in key_blocks:
                key_blocks[shape_key_name].value = value
                # message = f"{shape_key_name} 셰이프 키 값을 {value}로 변경함"
                # show_info_message(message)
            else:
                message = f"{shape_key_name} 셰이프 키를 찾을 수 없음"
                show_info_message(message)



def get_character_items(self, context):
    mytool = context.scene.my_tool

    if mytool.base_body_type == 'LOLI':
        return []#('DIONA', "디오나", "Diona"),
                #('DORI', "도리", "Dori"),
                #('KLEE', "클레", "Klee"),
                #('KLEEALT', "클레 마녀", "Klee Alt"),
                #('NAHIDA', "나히다", "Nahida"),
                #('QIQI', "치치", "Qiqi"),
                #('SAYU', "사유", "Sayu"),
                #('YAOYAO', "요요", "YaoYao")]
    elif mytool.base_body_type == 'TEEN':
        return [#('AMBER', "앰버", "Amber"),
                #('AMBERCN', "앰버 검열", "AmberCN"),
                #('AYAKA', "아야카", "Ayaka"),
                #('BARBARA', "바바라", "Barbara"),
                #('BARBARAALT', "바바라 스킨", "Barbara Alt"),
                ('CHARLOTTE', "샤를로트", "Charlotte"),
                #('COLLEI', "콜레이", "Collei"),
                #('FARUZAN', "파루잔", "Faruzan"),
                #('FISCHL', "피슬", "Fischl"),
                #('FISCHLALT', "피슬 스킨", "Fischl Alt"),
                ('FURINA', "푸리나", "Furina"),
                #('GANYU', "감우", "Ganyu"),
                #('HUTAO', "호두", "HuTao"),
                #('KEQING', "각청", "Keqing"),
                #('KEQINGALT', "각청 스킨", "Keqing Alt"),
                #('KIRARA', "키라라", "Kirara"),
                #('KOKOMI', "코코미", "Kokomi"),
                #('LAYLA', "레일라", "Layla"),
                #('LYNETTE', "리넷", "Lynette"),
                ('MONA', "모나", "Mona"),]
                #('MONACN', "모나 검열", "MonaCN"),
                #('NILOU', "닐루", "Nilou"),
                #('NOELLE', "노엘", "Noelle"),
                #('SHINOBU', "시노부", "Shinobu"),
                #('SUCROSE', "설탕", "Sucrose"),
                #('LUMINE', "여행자", "TravelerGirl"),
                #('XIANGLING', "향릉", "Xiangling"),
                #('XINYAN', "신염", "Xinyan"),
                #('YANFEI', "연비", "Yanfei"),
                #('YOIMIYA', "요이미야", "Yoimiya"),
                #('YUNJIN', "운근", "YunJin")]
    elif mytool.base_body_type == 'ADULT':
        return []#('BEIDOU', "북두", "Beidou"),
                #('CANDACE', "캔디스", "Candace"),
                #('DEHYA', "데히야", "Dehya"),
                #('EULA', "유라", "Eula"),
                #('JEAN', "진", "Jean"),
                #('JEANCN', "진 검열", "JeanCN"),
                #('JEANSEA', "진 스킨", "Jean Alt"),
                #('KUJOUSARA', "쿠죠 사라", "KujouSara"),
                #('LISA', "리사", "Lisa"),
                #('LISAALT', "리사 스킨", "Lisa Alt"),
                #('NINGGUANG', "응광", "Ningguang"),
                #('NINGGUANGALT', "응광 스킨", "Ningguang Alt"),
                #('RAIDEN', "라이덴", "RaidenShogun"),
                #('ROSARIA', "로자리아", "Rosaria"),
                #('ROSARIACN', "로자리아 검열", "RosariaCN"),
                #('SHENHE', "신학", "Shenhe"),
                #('YAE', "야에 미코", "Yae"),
                #('YELAN', "야란", "Yelan")]
    else:
        return []




class ExecuteAuxClassOperator(bpy.types.Operator):
    """Export full animation frame by frame. System console recomended."""
    bl_idname = "my.execute_auxclass_aux"
    bl_label = "Export Mod Aux"

    def exportframe(self,context,filename):
        scene = context.scene
        my_tool = scene.my_tool
        dirPath = os.path.dirname(my_tool.ExportFile)
        object_name = os.path.basename(dirPath)
        try:
            HeadName = None
            BodyName = None
            DressName = None
            ExtraName = None
            if not [obj for obj in scene.objects if object_name.lower() in obj.name.lower()]:
                raise Fatal("일치하는 이름을 찾을 수 없습니다. 원본 데이터 폴더에 ObjectName.vb로 내보내고 있는지, ObjectName 이 장면에 존재하고 해시.json이 있는지 다시 확인하세요")
            for obj in scene.objects:
                if object_name.lower()+"head" in obj.name.lower() and obj.visible_get():
                    HeadName = obj.name
                elif object_name.lower()+"body" in obj.name.lower() and obj.visible_get():
                    BodyName = obj.name
                elif object_name.lower()+"dress" in obj.name.lower() and obj.visible_get():
                    DressName = obj.name
                elif object_name.lower()+"extra" in obj.name.lower() and obj.visible_get():
                    ExtraName = obj.name

            
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True, animation=True, obdata_animation=True)
            # checks if the collections exist before joining. otherwise doesnt join
            if(HeadName is not None):
                self.joinInto(scene.Head, HeadName)
            if(BodyName is not None):
                self.joinInto(scene.Body, BodyName)
            if(DressName is not None):
                self.joinInto(scene.Dress, DressName)
            if(ExtraName is not None):
                self.joinInto(scene.Extra, ExtraName)
            
            filepath = dirPath + "/" + object_name + ".vb"
            if(filename is not None):
                path=dirPath
                filepath = path +"/"+ filename
            vb_path = filepath
            ib_path = os.path.splitext(vb_path)[0] + '.ib'
            fmt_path = os.path.splitext(vb_path)[0] + '.fmt'

            Outline_Properties = (my_tool.outline_optimization, my_tool.toggle_rounding_outline, my_tool.decimal_rounding_outline, my_tool.angle_weighted, my_tool.overlapping_faces, my_tool.detect_edges, my_tool.calculate_all_faces, my_tool.nearest_edge_distance)
            export_3dmigoto_genshin(self, context, object_name, vb_path, ib_path, fmt_path, my_tool.use_foldername, my_tool.ignore_hidden, my_tool.only_selected, my_tool.no_ramps, my_tool.delete_intermediate, my_tool.credit,Outline_Properties)
            bpy.ops.ed.undo_push(message="Joining Meshes and Exporting Mod Folder")
            bpy.ops.ed.undo()
        except Fatal as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}
    
    def execute(self, context):
        scene = context.scene

        if scene.my_tool.ExportFile:
            self.exportframe(bpy.context, None)
        else:
            message = "Export 경로가 지정되지 않았습니다."
            show_info_message(message)
            return {'CANCELLED'}

        return {'FINISHED'}
        
    def appendto(self, collection, destination):
        for a_collection in collection.children:
            self.appendto(a_collection, destination)
        for obj in collection.objects:
            if obj.type == "MESH":
                destination.append(obj)

    def joinInto(self, collection_name, target_obj_name):
        target_obj = bpy.data.objects[target_obj_name]
        objects_to_join = []
        if collection_name is not None:
            collection_obj = bpy.data.collections[collection_name.name]
            #recursively appends elements within the collection
            self.appendto(collection_obj, objects_to_join)

        #select main object then selecting all the meshes to join into it
        bpy.data.objects[target_obj_name].select_set(True)
        if len(objects_to_join) > 0:
            for obj in objects_to_join:
                obj.select_set(True)
        #apply shapekeys
        context = bpy.context
        objs = context.selected_objects
        for ob in objs:
            ob.hide_viewport = False  # should be visible
            if ob.data.shape_keys:
                 ob.shape_key_add(name='CombinedKeys', from_mix=True)
                 for shapeKey in ob.data.shape_keys.key_blocks:
                     ob.shape_key_remove(shapeKey)
        #apply modifierss
        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = obj
            for modifier in obj.modifiers:
                if not modifier.show_viewport:
                    obj.modifiers.remove(modifier)
                else:
                    bpy.ops.object.modifier_apply(modifier=modifier.name)
                
        bpy.context.view_layer.objects.active = target_obj
        #join
        bpy.ops.object.join()
        target_obj.data = bpy.context.object.data
        
        #quick fix to remove all vertex groups with the word MASK on them
        #lacks user interface and feedback 
        ob = target_obj
        vgs = [vg for vg in ob.vertex_groups
               if vg.name.find("MASK") != -1]
        while(vgs):
            ob.vertex_groups.remove(vgs.pop())
            
        #deselect everything and set result as active
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = target_obj
        return {'FINISHED'}

class ES_ExecuteAuxClassOperator(ExecuteAuxClassOperator):
    bl_idname = "my.execute_auxclass"
    bl_label = "Export Mod"

class ExportAnimationOperator(ExecuteAuxClassOperator):
    """Operator to execute the auxClass"""
    bl_idname = "my.exportanimation"
    bl_label = "Export animation"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="정말 애니메이션으로 내보내시겠습니까? 도중에 중지할 수 없습니다.")

    def execute(self,context):
        bpy.ops.ed.undo_push(message="Exporting Animation!")
        scene = context.scene
        my_tool = scene.my_tool        
        dirPath = os.path.dirname(my_tool.ExportFile)
        object_name = os.path.basename(dirPath)
        filepath = dirPath+"/"+object_name+".vb"

        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        print("starting animation exporting Loop")
        for f in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(f)
            filename = "%sf%04d.vb" % (object_name, f)
            self.exportframe(bpy.context, filename)
            
            dirname = os.path.dirname(filepath)+"Mod"
            new = dirname+"f%04d" % f
            
            if os.path.exists(new):
                os.remove(new)
            os.rename(dirname, new)
            print("exported: "+filename)
        
        directory = os.path.dirname(os.path.dirname(filepath))
        newfile_name = os.path.join( directory , "genshin_merge_mods.py")
        newfile_name2 = os.path.join( directory , "speedControl.py")

        file1_args = ["-c","-k y"]
        file2_args = ["-s {}".format(frame_start), "-e {}".format(frame_end)]
        file1_command = ["python", newfile_name] + file1_args
        file2_command = ["python", newfile_name2] + file2_args
        try:
            file1_process = subprocess.Popen(file1_command, stdin=subprocess.PIPE, cwd=directory)
            file1_process.communicate(input=b"\n")
            file1_process.wait()
            subprocess.run(file2_command, check=True, stdin=subprocess.PIPE, cwd=directory)
        except subprocess.CalledProcessError as e:
            print(f"Error running file2.py: {e}")
        return {'FINISHED'}




classes = (
    ImportBaseBody,
    ExecuteAuxClassOperator,
    ES_ExecuteAuxClassOperator,
    ExportAnimationOperator,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)