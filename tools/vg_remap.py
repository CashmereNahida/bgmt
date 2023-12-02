import bpy

import os
import platform
import subprocess
import configparser
from collections import defaultdict
import mathutils
import numpy as np
import re





def update_remap_version(self, context):
    mytool = context.scene.my_tool

    remap_version = mytool.remap_version
    set_advanced_settings = mytool.set_advanced_settings
    
    items = [
        ('version1', 'v1-original', 'SilentNightSound#7430 가 작성한 Original VG_Remap 입니다'),
        ('version2', 'v2-kusaknee', 'github/kusaknee 가 수정한 VG_Remap 입니다. 대부분의 상황에서 v1 대비 더 정교한 리맵을 시도합니다'),
    ]
    
    if set_advanced_settings:
        items.append(('version3', 'v3', '커스텀 리맵과 가중치 색적 거리 변경, 인터폴레이션을 지원함'))
    
    mytool.remap_version[1]['items'] = items
    
    if remap_version not in [item[0] for item in items]:
        mytool.remap_version = items[-1][0]

def get_remap_version_items(self, context):
    mytool = context.scene.my_tool

    set_advanced_settings = mytool.set_advanced_settings
    
    items = [
        ('version2', 'v2-kusaknee', 'github/kusaknee 가 수정한 VG_Remap 입니다. 대부분의 상황에서 v1 대비 더 정교한 리맵을 시도합니다'),
        ('version1', 'v1-original', 'SilentNightSound#7430 가 작성한 Original VG_Remap 입니다'),
    ]
    
    if set_advanced_settings:
        items.append(('version3', 'v3', '커스텀 리맵과 가중치 색적 거리 변경, 인터폴레이션을 지원함'))
    
    return items






current_file_path = os.path.dirname(os.path.realpath(__file__))
ini_file_path = os.path.join(current_file_path, 'characters.ini')
print(ini_file_path)

def open_file(file_path):
    if platform.system() == "Windows":
        os.startfile(file_path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", file_path])
    elif platform.system() == "Linux":
        subprocess.Popen(["xdg-open", file_path])

def get_ini_file_path():
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_file_path, 'characters.ini')

def get_character_names_from_ini(self, context):
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    ini_file_path = os.path.join(current_file_path, 'characters.ini')

    config = configparser.ConfigParser()
    try:
        with open(ini_file_path, 'r', encoding='utf-8') as f:
            config.read_file(f)
    except Exception as e:
        print(f"Failed to read ini file. Reason: {e}")
        return []

    names = []

    for section in config.sections():
        split_names = section.split(',')
        if len(split_names) == 3:
            identifier, name, description = split_names
            names.append((identifier.strip(), name.strip(), description.strip()))

    return names

# Returns position, vertex group and weight data for all vertices in object
def collect_vertices(obj):
    results = {}
    for v in obj.data.vertices:
        results[(v.co.x, v.co.y, v.co.z)] = [(vg.group, vg.weight) for vg in v.groups]
    return results

# Finds the nearest group for a specified weight
def nearest_group(weight, nearest_source):
    nearest_group = -1
    smallest_difference = 10000000000
    for source_group, source_weight in nearest_source:
        if abs(weight - source_weight) < smallest_difference:
            smallest_difference = abs(weight - source_weight)
            nearest_group = source_group
    return nearest_group, smallest_difference

def vgremap_v3_weights(source_object, destination_object, REF_DEST, weighted, MERGE_VG, TOLERANCE=0.1, alpha=0.5, character_name="", skip_numeric_vg=False, custom_remap=False, v3_advanced=False):

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(ini_file_path)

    section_to_first_name = {section: section.split(',')[0].strip() for section in config.sections()}

    if character_name not in section_to_first_name.values():
        print(f"'{character_name}' 이름의 캐릭터가 ini 파일에 없습니다.")
        return {'CANCELLED'}

    if custom_remap and skip_numeric_vg:
        actual_section_name = [key for key, value in section_to_first_name.items() if value == character_name][0]
        remap_data = dict(config[actual_section_name])
        for vg in destination_object.vertex_groups:
            if vg.name in remap_data:
                vg.name = remap_data[vg.name]

    if not source_object or not destination_object:
        print("Source or destination object is missing!")
        return {'CANCELLED'}
    
    if not REF_DEST:
        REF_DEST = destination_object

    def merge_vgs(obj):
        vg_index_to_name = {}
        vg_name_to_index = {}
        for vg in obj.vertex_groups:
            vg_index_to_name[vg.index] = vg.name
            vg_name_to_index[vg.name] = vg.index

        vg_to_vertex = defaultdict(lambda: defaultdict(float))
        for v in obj.data.vertices:
            for vg in v.groups:
                vg_name = vg_index_to_name.get(vg.group, '')
                if '.' not in vg_name:
                    continue

                main_name = vg_name.split('.')[0]
                vg_to_vertex[main_name][v.index] += vg.weight

        for vg, vidx_to_weight in vg_to_vertex.items():
            if vg not in vg_name_to_index:
                continue

            vg_ref = obj.vertex_groups[vg_name_to_index[vg]]
            for vidx, weight in vidx_to_weight.items():
                vg_ref.add([vidx], weight, 'ADD')

        for vg in obj.vertex_groups:
            if '.' in vg.name:
                obj.vertex_groups.remove(vg)

    def calc_center_of_mass_per_vg(obj, weighted=False):
        index_to_name = {}
        for vg in obj.vertex_groups:
            index_to_name[vg.index] = vg.name

        vertices_per_group = {}
        for v in obj.data.vertices:
            for vg in v.groups:
                if vg.weight == 0:
                    continue

                if vg.group not in index_to_name:
                    raise ValueError(f'Vertex has vertex group with index {vg.group} but this is not known.')

                vg_name = index_to_name[vg.group]

                if vg_name not in vertices_per_group:
                    vertices_per_group[vg_name] = [[], []]

                weight = vg.weight if weighted else 1.0
                vv = obj.matrix_world @ v.co

                vertices_per_group[vg_name][0].append(vv)
                vertices_per_group[vg_name][1].append(weight)

        cm_per_group = {}
        size_per_group = {}
        shape_per_group = {}

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
            if v3_advanced:
                size_per_group[vg_name] = calc_group_size(vertices)
                shape_per_group[vg_name] = calc_group_shape(vertices)


        return cm_per_group, size_per_group, shape_per_group

    def init_kdtree_vertex_to_cm(vg_to_vertex):
        kd_size = len(vg_to_vertex.keys()) #1086
        kd = mathutils.kdtree.KDTree(kd_size)

        idx_to_vggroup = {}

        for idx, (vg, vert) in enumerate(vg_to_vertex.items()):
            kd.insert(vert, idx)
            idx_to_vggroup[idx] = vg

        kd.balance()

        return kd, idx_to_vggroup

    if v3_advanced:
        def calc_group_size(vertices):
            centroid = np.mean(vertices, axis=0)
            distances = np.linalg.norm(vertices - centroid, axis=1)
            return np.mean(distances)

        def calc_group_shape(vertices):
            data = np.array(vertices)
            mean = np.mean(data, axis=0)
            data_centered = data - mean
            _, s, _ = np.linalg.svd(data_centered)
            while len(s) < 3:
                s = np.append(s, 0)
            return s

        def interpolate(val1, val2, alpha=0.5):
            return val1 * (1 - alpha) + val2 * alpha

    def calc_best_candidates(source_obj, dest_obj, weighted=False, TOLERANCE=0.1, alpha=0.5, v3_advanced=False):
        best = {}

        if v3_advanced:
            source_cm, source_sizes, source_shapes = calc_center_of_mass_per_vg(source_obj, weighted)
            source_kd, source_idx_to_vggroup = init_kdtree_vertex_to_cm(source_cm)

            dest_cm, dest_sizes, dest_shapes = calc_center_of_mass_per_vg(dest_obj, weighted)

            remap_data = {}

            for idx, (vg_group, cm) in enumerate(dest_cm.items()):
                if skip_numeric_vg and vg_group in remap_data.values():
                    continue
                nearest_points = source_kd.find_range(cm, TOLERANCE)
                if not nearest_points:
                    continue

                best_similarity = float('inf')
                best_vg_name = None

                for _, idx, dist in nearest_points:
                    vg_name = source_idx_to_vggroup[idx]

                    size_diff = abs(dest_sizes[vg_group] - source_sizes[vg_name])
                    if v3_advanced:
                        shape_diff = np.linalg.norm(dest_shapes[vg_group] - source_shapes[vg_name])
                        interpolated_diff = interpolate(dist, interpolate(size_diff, shape_diff, alpha=alpha), alpha=alpha)
                    else:
                        interpolated_diff = dist

                    if interpolated_diff < best_similarity:
                        best_similarity = interpolated_diff
                        best_vg_name = vg_name

                if best_vg_name:
                    best[vg_group] = best_vg_name

        else:
            source_cm, _, _ = calc_center_of_mass_per_vg(source_obj, weighted)  # Unpack the tuple and use the first element
            source_kd, source_idx_to_vggroup = init_kdtree_vertex_to_cm(source_cm)  # Use the dictionary

            dest_cm, _, _ = calc_center_of_mass_per_vg(dest_obj, weighted)  # Ignore the other parts of the tuple
            for idx, (vg_group, cm) in enumerate(dest_cm.items()):
                _, idx, _ = source_kd.find(cm)
                best[vg_group] = source_idx_to_vggroup[idx]

        return best

    if not source_object or not destination_object:
        print("Source or destination object is missing!")
        return {'CANCELLED'}
    
    if not REF_DEST:
        REF_DEST = destination_object

    def is_excluded_vg_name(name):
        return bool(re.match(r"^\d+(\.\d{3})?$", name))

    def main(source, destination, ref_destination, weighted, MERGE_VG, v3_advanced=False):
        source_object = bpy.data.objects[source]
        destination_object = bpy.data.objects[destination]
        ref_destination_object = bpy.data.objects[ref_destination]

        best = calc_best_candidates(source_object, ref_destination_object, weighted=weighted, TOLERANCE=TOLERANCE, alpha=alpha) #1181

        for vg in destination_object.vertex_groups:
            if vg.name.isdigit() or re.match(r"^\d+\.\d{3}$", vg.name):
                continue

            if vg.name not in best:
                destination_object.vertex_groups.remove(vg)
                continue

            new_name = best[vg.name]
            if custom_remap and character_name and new_name in remap_data:
                new_name = remap_data[new_name]
            vg.name = f'x{new_name}'

        for vg in destination_object.vertex_groups:
            if vg.name.startswith('x'):
                if vg.name[1:].isdigit() or re.match(r"^\d+\.\d{3}$", vg.name[1:]):
                    vg.name = vg.name[1:]
                else:
                    vg.name = vg.name[1:]

        missing_groups = set([f'x{group}' for group in source_object.vertex_groups.keys()]) - set([vg.name for vg in destination_object.vertex_groups])
        for group in missing_groups:
            destination_object.vertex_groups.new(name=group[1:])

        destination_object.vertex_groups.update()

        if MERGE_VG:
            merge_vgs(destination_object)

        bpy.context.view_layer.objects.active = destination_object
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.vertex_group_sort(sort_type='NAME')

        return {'FINISHED'}

    return main(source_object.name, destination_object.name, REF_DEST.name, weighted, MERGE_VG, v3_advanced)

def vgremap_v2_weights(source_object, destination_object, REF_DEST, weighted, MERGE_VG):
# take from https://github.com/kusaknee/gimi_scripts/blob/master/vg_remap.py

    def merge_vgs(obj):
        vg_index_to_name = {}
        vg_name_to_index = {}
        for vg in obj.vertex_groups:
            vg_index_to_name[vg.index] = vg.name
            vg_name_to_index[vg.name] = vg.index

        vg_to_vertex = defaultdict(lambda: defaultdict(float))
        for v in obj.data.vertices:
            for vg in v.groups:
                vg_name = vg_index_to_name.get(vg.group, '')
                # Reduce memory footprint by only storing vgs we are likely to pop.
                if '.' not in vg_name:
                    continue

                main_name = vg_name.split('.')[0]

                vg_to_vertex[main_name][v.index] += vg.weight

        for vg, vidx_to_weight in vg_to_vertex.items():
            if vg not in vg_name_to_index:
                continue

            vg_ref = obj.vertex_groups[vg_name_to_index[vg]]
            for vidx, weight in vidx_to_weight.items():
                vg_ref.add([vidx], weight, 'ADD')

        for vg in obj.vertex_groups:
            if '.' in vg.name:
                obj.vertex_groups.remove(vg)

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
                    raise ValueError(f'Vertex has vertex group with index {vg.group} but this is not known.')

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

    def init_kdtree_vertex_to_cm(vg_to_vertex):
        kd_size = len(vg_to_vertex.keys())
        kd = mathutils.kdtree.KDTree(kd_size)

        idx_to_vggroup = {}

        for idx, (vg, vert) in enumerate(vg_to_vertex.items()):
            kd.insert(vert, idx)
            idx_to_vggroup[idx] = vg

        kd.balance()

        return kd, idx_to_vggroup


    def calc_best_candidates(source_obj, dest_obj, weighted=False):
        best = {}

        source_cm = calc_center_of_mass_per_vg(source_obj, weighted)
        source_kd, source_idx_to_vggroup = init_kdtree_vertex_to_cm(source_cm)

        dest_cm = calc_center_of_mass_per_vg(dest_obj, weighted)
        for idx, (vg_group, cm) in enumerate(dest_cm.items()):
            _, idx, _ = source_kd.find(cm)
            best[vg_group] = source_idx_to_vggroup[idx]
        
        return best

    if not source_object or not destination_object:
        print("Source or destination object is missing!")
        return {'CANCELLED'}
    
    if not REF_DEST:
        REF_DEST = destination_object

    def main(source, destination, ref_destination, weighted, MERGE_VG):

        if source not in bpy.data.objects or destination not in bpy.data.objects:
            print("Source or Destination objects don't exist in the current Blender data!")
            return {'CANCELLED'}
        
        source_object = bpy.data.objects[source]
        destination_object = bpy.data.objects[destination]

        if not ref_destination or ref_destination not in bpy.data.objects:
            ref_destination = destination
        ref_destination_object = bpy.data.objects[ref_destination]
        
        best = calc_best_candidates(source_object, ref_destination_object, weighted=weighted)

        # And then go through the list of vertex groups and rename them
        # In order to reduce name conflicts, we add an "x" in front and then remove it later
        # Blender automatically renames duplicate vertex groups by adding .0001, .0002, etc.
        for vg in destination_object.vertex_groups:
            if vg.name not in best:
                destination_object.vertex_groups.remove(vg)
                continue

            vg.name = f'x{best[vg.name]}'

        for vg in destination_object.vertex_groups:
            vg.name = vg.name[1:]
        
        # Finally, fill in missing spots and sort vertex groups 
        missing_groups = set([f"{vg.name}" for vg in source_object.vertex_groups]) - set([x.name.split(".")[0] for x in destination_object.vertex_groups])
        for missing_group in missing_groups:
            destination_object.vertex_groups.new(name=f"{missing_group}")

        if MERGE_VG:
            merge_vgs(destination_object)
        
        # I'm not sure if it is possible to sort/add vertex groups without setting the current object and using ops
        bpy.context.view_layer.objects.active = destination_object
        bpy.ops.object.vertex_group_sort()

    main(source_object.name, destination_object.name, REF_DEST.name, weighted, MERGE_VG)

    return {'FINISHED'}

def vgremap_v1_weights(source_object, destination_object):

    original_vg_length = len(source_object.vertex_groups)

    # Collect all the vertices in the source along with their corresponding non-zero weight vertex groups
    source_vertices = collect_vertices(source_object)
    tree = KDTree(list(source_vertices.keys()), 3)

    # Then, go through each of the vertex groups in destination and keep a running tally of how different a given source
    #   vertex is from the destination
    candidates = [{} for _ in range(len(destination_object.vertex_groups))]
    destination_vertices = collect_vertices(destination_object)
    for vertex in destination_vertices:
        nearest_source = source_vertices[tree.get_nearest(vertex)[1]]
        for group, weight in destination_vertices[vertex]:
            if weight == 0:
                continue
            nearest_source_group, smallest_distance = nearest_group(weight, nearest_source)
            # I originally recorded both the sum and count to do an averaged weighting, but just using the count
            #    alone gives better results in most cases
            if nearest_source_group in candidates[group]:
                x = candidates[group][nearest_source_group]
                candidates[group][nearest_source_group] = [x[0] + smallest_distance, x[1] + 1]
            else:
                candidates[group][nearest_source_group] = [smallest_distance, 1]

    # Next, we need to choose the best match from the candidates
    best = []
    for group in candidates:
        best_group = -1
        highest_overlap = -1
        for c in group:
            if group[c][1] > highest_overlap:
                best_group = c
                highest_overlap = group[c][1]
        best.append(best_group)

    # And then go through the list of vertex groups and rename them
    # In order to reduce name conflicts, we add an "x" in front and then remove it later
    # Blender automatically renames duplicate vertex groups by adding .0001, .0002, etc.
    for i, vg in enumerate(destination_object.vertex_groups):
        if best[i] == -1:
            print(f"Removing empty group {vg.name}")
            destination_object.vertex_groups.remove(vg)
        else:
            print(f"Renaming {vg.name} to {best[i]}")
            vg.name = f"x{str(best[i])}"

    for i, vg in enumerate(destination_object.vertex_groups):
        vg.name = vg.name[1:]
    
    # Finally, fill in missing spots and sort vertex groups 
    missing = set([f"{i}" for i in range(original_vg_length)]) - set([x.name.split(".")[0] for x in destination_object.vertex_groups])
    for number in missing:
        destination_object.vertex_groups.new(name=f"{number}")
    
    # I'm not sure if it is possible to sort/add vertex groups without setting the current object and using ops
    bpy.context.view_layer.objects.active = destination_object
    bpy.ops.object.vertex_group_sort()

class SIMPLE_OT_OpenINI(bpy.types.Operator):
    bl_idname = "simple.open_ini"
    bl_label = "Open INI File"

    def execute(self, context):
        ini_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'characters.ini')
        if os.path.exists(ini_file_path):
            open_file(ini_file_path)
        else:
            self.report({'ERROR'}, "INI file not found!")
        return {'FINISHED'}
    
class SIMPLE_OT_refresh_enum(bpy.types.Operator):
    bl_idname = "simple.refresh_enum"
    bl_label = "Refresh Character List"

    def update_character_enum(self, context):
        global character_name
        character_name[1]['items'] = get_character_names_from_ini(context)

# https://github.com/Vectorized/Python-KD-Tree
class KDTree(object):

    def __init__(self, points, dim, distance_mode='euclidean', post_processing=False):
        self.post_processing = post_processing

        # ߟ᠓elect distance calculation based on the mode
        if distance_mode == 'euclidean':
            dist_func = lambda a, b: sum((x - b[i]) ** 2 for i, x in enumerate(a))
        elif distance_mode == 'manhattan':
            dist_func = lambda a, b: sum(abs(x - b[i]) for i, x in enumerate(a))
        elif distance_mode == 'cosine':
            dot = lambda u, v: sum(x*y for x, y in zip(u, v))
            norm = lambda v: (sum(x*x for x in v)) ** 0.5
            dist_func = lambda a, b: 1 - dot(a, b) / (norm(a) * norm(b))
        else:
            raise ValueError(f"Unsupported distance mode: {distance_mode}")

        # [Original KDTree initialization code]

        def make(points, i=0):
            if len(points) > 1:
                points.sort(key=lambda x: x[i])
                i = (i + 1) % dim
                m = len(points) >> 1
                return [make(points[:m], i), make(points[m + 1:], i), points[m]]
            if len(points) == 1:
                return [None, None, points[0]]

        def add_point(node, point, i=0):
            if node is not None:
                dx = node[2][i] - point[i]
                for j, c in ((0, dx >= 0), (1, dx < 0)):
                    if c and node[j] is None:
                        node[j] = [None, None, point]
                    elif c:
                        add_point(node[j], point, (i + 1) % dim)

        import heapq
        def get_knn(node, point, k, return_dist_sq, heap, i=0, tiebreaker=1):
            if node is not None:
                dist_sq = dist_func(point, node[2])
                dx = node[2][i] - point[i]
                if len(heap) < k:
                    heapq.heappush(heap, (-dist_sq, tiebreaker, node[2]))
                elif dist_sq < -heap[0][0]:
                    heapq.heappushpop(heap, (-dist_sq, tiebreaker, node[2]))
                i = (i + 1) % dim
                for b in (dx < 0, dx >= 0)[:1 + (dx * dx < -heap[0][0])]:
                    get_knn(node[b], point, k, return_dist_sq, heap, i, (tiebreaker << 1) | b)
            if tiebreaker == 1:
                return [(-h[0], h[2]) if return_dist_sq else h[2] for h in sorted(heap)][::-1]

        def walk(node):
            if node is not None:
                for j in 0, 1:
                    for x in walk(node[j]):
                        yield x
                yield node[2]

        self._add_point = add_point
        self._get_knn = get_knn
        self._root = make(points)
        self._walk = walk

    def __iter__(self):
        return self._walk(self._root)

    def add_point(self, point):
        if self._root is None:
            self._root = [None, None, point]
        else:
            self._add_point(self._root, point)

    def get_knn(self, point, k, return_dist_sq=True):
        results = self._get_knn(self._root, point, k, return_dist_sq, [])

        # ߟ᠁pply post-processing if enabled
        if self.post_processing:
            results = self._apply_antialiasing(results)

        return results

    # ߟ᠁dded method for Anti-Aliasing post-processing
    def _apply_antialiasing(self, results):
        if not results:
            return results
        avg_point = [sum(pt[i] for _, pt in results) / len(results) for i in range(len(results[0][1]))]
        return [(res[0], avg_point) for res in results]

    def get_nearest(self, point, return_dist_sq=True):
        l = self._get_knn(self._root, point, 1, return_dist_sq, [])
        return l[0] if len(l) else None


classes = (
    SIMPLE_OT_OpenINI,
    SIMPLE_OT_refresh_enum,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)