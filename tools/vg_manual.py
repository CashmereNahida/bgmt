import bpy
import blf
import mathutils
from mathutils import Vector
from collections import defaultdict
import bpy_extras.view3d_utils
from .._utils import show_info_message


source_vertex_group_centers = {}
target_vertex_group_centers = {}
global_draw_handler = None
global drawing_started
drawing_started = False
global text_positions
text_positions = {}


def merge_vgs(obj, selected_vg_name):
    base_name = selected_vg_name.split('.')[0]

    vg_index_to_name = {}
    vg_name_to_index = {}
    for vg in obj.vertex_groups:
        vg_index_to_name[vg.index] = vg.name
        vg_name_to_index[vg.name] = vg.index

    merge_target_names = [vg.name for vg in obj.vertex_groups if vg.name.startswith(base_name + ".") or vg.name == base_name]
    merge_target_indices = [vg_name_to_index[name] for name in merge_target_names if name in vg_name_to_index]

    for v in obj.data.vertices:
        total_weight = sum(vg.weight for vg in v.groups if vg.group in merge_target_indices)
        if total_weight > 0:
            obj.vertex_groups[base_name].add([v.index], total_weight, 'REPLACE')

    for name in merge_target_names:
        if name != base_name:
            obj.vertex_groups.remove(obj.vertex_groups[name])

def calc_center_of_mass_per_vg(obj, weighted=False):
    index_to_name = {}
    # Vertices contain information only on vertex group index, not names.
    for vg in obj.vertex_groups:
        index_to_name[vg.index] = vg.name

    vertices_per_group = {}
    for v in obj.data.vertices:
        for vg in v.groups:
            if vg.weight == 0:
                continue

            if vg.group not in index_to_name:
                # Well, something went wrong.
                show_info_message(f"Vertex has vertex group with index {vg.group} but this is not known.")

            vg_name = index_to_name[vg.group]

            if vg_name not in vertices_per_group:
                vertices_per_group[vg_name] = [[], []]

            weight = vg.weight if weighted else 1.0

            vv = obj.matrix_world @ v.co

            vertices_per_group[vg_name][0].append(vv)
            vertices_per_group[vg_name][1].append(weight)

    cm_per_group = {}

    for vg_name, (vertices, weights) in vertices_per_group.items():
        summed_weights = sum(weights)

        if summed_weights == 0:
            continue

        vw = zip(vertices, weights)

        x_center = 0.0
        y_center = 0.0
        z_center = 0.0

        for p, w in zip(vertices, weights):
            x_center += p.x * w
            y_center += p.y * w
            z_center += p.z * w

        x_center /= summed_weights
        y_center /= summed_weights
        z_center /= summed_weights

        cm_per_group[vg_name] = (x_center, y_center, z_center)

    return cm_per_group

def init_kdtree_vertex_group_centers(vertex_group_centers):
    kd = mathutils.kdtree.KDTree(len(vertex_group_centers))
    idx_to_vgname = {}

    for idx, (vg_name, center) in enumerate(vertex_group_centers.items()):
        kd.insert(center, idx)
        idx_to_vgname[idx] = vg_name

    kd.balance()
    return kd, idx_to_vgname

def draw_callback_px(self, context):
    global text_positions
    text_positions.clear()
    font_id = 0
    target_obj = context.active_object

    if target_obj and target_obj.type == 'MESH' and target_obj.vertex_groups.active:
        active_group_name = target_obj.vertex_groups.active.name
        target_center = target_vertex_group_centers.get(active_group_name)

        if target_center:
            closest_groups = self.source_kdtree.find_n(target_center, self.num_closest_groups)
            
            for (_, idx, _) in closest_groups:
                vg_name = self.idx_to_vgname[idx]
                center = source_vertex_group_centers[vg_name]
                x, y = draw_text(vg_name, center, font_id, self.font_size)
                if x is not None and y is not None:
                    text_positions[vg_name] = (x, y)


def draw_text(text, position, font_id, font_size):
    x, y = bpy_extras.view3d_utils.location_3d_to_region_2d(bpy.context.region, bpy.context.region_data, position)
    if x is not None and y is not None:
        blf.size(font_id, font_size)
        text_width, text_height = blf.dimensions(font_id, text)

        x -= text_width / 2
        y -= text_height / 2

        blf.position(font_id, x, y, 0)
        blf.draw(font_id, text)
        return x, y
    return None, None



class StartDrawingVertexGroups(bpy.types.Operator):
    """Draw Closest Vertex Groups"""
    bl_idname = "vertex.draw_closest_vertex_groups"
    bl_label = "Draw Closest Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):
        global drawing_started
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            mytool = context.scene.my_tool
            if mytool.quick_mapping and drawing_started:
                return self.handle_left_mouse_click(context, event)

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            mytool = context.scene.my_tool
            if mytool.quick_mapping:
                self.cancel(context)
                drawing_started = False
                return {'CANCELLED'}
            
        # Ctrl 키와 마우스 휠을 사용한 정점 그룹 변경
        if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.ctrl:
            target_obj = context.active_object
            if target_obj and target_obj.type == 'MESH' and target_obj.vertex_groups:
                current_vg_index = target_obj.vertex_groups.active_index
                new_vg_index = self.get_new_vg_index(target_obj, current_vg_index, event.type)
                target_obj.vertex_groups.active_index = new_vg_index
                return {'RUNNING_MODAL'}

        return {'PASS_THROUGH'}
        
    def cancel(self, context):
        global global_draw_handler
        if global_draw_handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(global_draw_handler, 'WINDOW')
            global_draw_handler = None

    def invoke(self, context, event):
        global source_vertex_group_centers, target_vertex_group_centers
        global global_draw_handler
        mytool = context.scene.my_tool

        source_obj = mytool.source_object
        target_obj = mytool.destination_object
        self.num_closest_groups = mytool.num_closest_groups
        self.font_size = mytool.font_size

        if not source_obj or not target_obj:
            show_info_message("메쉬를 지정하고 다시 시도하세요")
            # self.report({'ERROR'}, "메쉬를 지정하세요")
            return {'CANCELLED'}

        source_vertex_group_centers = calc_center_of_mass_per_vg(source_obj, weighted=True)
        target_vertex_group_centers = calc_center_of_mass_per_vg(target_obj, weighted=True)

        self.source_kdtree, self.idx_to_vgname = init_kdtree_vertex_group_centers(source_vertex_group_centers)

        args = (self, context)
        global_draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        global drawing_started
        drawing_started = True
        return {'RUNNING_MODAL'}
    
    def handle_left_mouse_click(self, context, event):
        global text_positions
        mouse_co = Vector((event.mouse_region_x, event.mouse_region_y))
        closest_distance = float('inf')
        closest_vg_name = None
        mytool = context.scene.my_tool

        # 저장된 글자 위치를 사용하여 마우스 위치와 가장 가까운 정점 그룹 찾기
        for vg_name, pos in text_positions.items():
            distance = (mouse_co - Vector(pos)).length
            if distance < closest_distance:
                closest_distance = distance
                closest_vg_name = vg_name

        # 가장 가까운 정점 그룹의 이름으로 target_obj의 활성 정점 그룹 이름 변경
        if closest_vg_name and mytool.destination_object:
            target_obj = mytool.destination_object
            if target_obj and target_obj.type == 'MESH' and target_obj.vertex_groups.active:
                target_obj.vertex_groups.active.name = closest_vg_name

                if context.scene.my_tool.quick_mapping_merge_vg:
                    merge_vgs(target_obj, closest_vg_name)

        return {'RUNNING_MODAL'}
    
    def get_new_vg_index(self, obj, current_index, wheel_direction):
        if wheel_direction == 'WHEELUPMOUSE':
            return (current_index - 1) % len(obj.vertex_groups)
        elif wheel_direction == 'WHEELDOWNMOUSE':
            return (current_index + 1) % len(obj.vertex_groups)
        else:
            return current_index

class StopDrawingVertexGroups(bpy.types.Operator):
    """Stop Drawing Closest Vertex Groups"""
    bl_idname = "vertex.stop_drawing_vertex_groups"
    bl_label = "Stop Drawing Vertex Groups"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        global global_draw_handler

        if global_draw_handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(global_draw_handler, 'WINDOW')
            global_draw_handler = None
            global drawing_started
            drawing_started = False
            return {'FINISHED'}

        show_info_message("메뉴얼 모드가 활성화되어 있지 않음")
        return {'CANCELLED'}


classes = (
    StartDrawingVertexGroups,
    StopDrawingVertexGroups
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.draw_handler = bpy.props.PointerProperty(name="Draw Handler", type=bpy.types.Object)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)