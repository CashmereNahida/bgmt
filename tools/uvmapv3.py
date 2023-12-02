#uvmap for 1.3.3

import bpy
import sys
import os
import traceback
import re

from PIL import Image, ImageOps
from math import ceil
import subprocess
from rectpack import *
import subprocess

import glob
import math
from itertools import product

# massage popup
def show_info_message(message):
    print(message)
    message_lines = message.split('\n')
    def draw(self, context):
        for line in message_lines:
            self.layout.label(text=line)
    bpy.context.window_manager.popup_menu(draw, title="Info", icon='INFO')


# 텍스쳐 저장
def save_texture(image, output_filepath, mesh_name, alpha_invert):
    try:
        base_name, extension = os.path.splitext(output_filepath)
        if mesh_name:
            sanitized_mesh_name = get_base_name(mesh_name)
            file_name = f"{base_name}{sanitized_mesh_name.capitalize()}Diffuse{extension}"
        else:
            file_name = output_filepath

        if alpha_invert:
            r, g, b, a = image.split()
            a = a.point(lambda p: 255 - p)
            image = Image.merge("RGBA", (r, g, b, a))

        image_filepath = bpy.path.abspath(file_name)

        image.save(image_filepath)
        print(f"병합된 텍스쳐가 {image_filepath}에 저장되었습니다.")
        return image_filepath
    except Exception as e:
        error_message = str(e)
        if "unknown file extension" in error_message:
            show_info_message("정상적이지 않은 파일 확장자입니다.")
        else:
            show_info_message(f"텍스쳐 저장 중 오류 발생: {error_message}")

def group_objects_by_name(objects):
    groups = {}
    for obj in objects:
        base_name = obj.name.split(".")[0]
        if base_name not in groups:
            groups[base_name] = []
        groups[base_name].append(obj)
    return groups

def get_unique_image_name(filepath):
    base_name = os.path.basename(filepath)
    unique_name, _ = os.path.splitext(base_name)
    unique_name = re.sub(r'\.\d+$', '', unique_name)
    return unique_name

# 메쉬에서 텍스쳐 텍스쳐 추출
def get_selected_meshes_images(objects, skip_matcap, skip_toon_texture):
    images = {}

    for obj in objects:
        if obj.type == 'MESH':
            for mat_slot in obj.material_slots:
                if mat_slot.material and mat_slot.material.use_nodes:
                    for node in mat_slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE':
                            # mmd shader matcap, toon 텍스쳐 노드 스킵
                            if (skip_matcap and node.name == 'mmd_toon_tex') or \
                               (skip_toon_texture and node.name == 'mmd_sphere_tex'):
                                continue

                            image = node.image
                            if image:
                                filepath = bpy.path.abspath(image.filepath)
                                if not os.path.exists(filepath):
                                    error_message = f"'{obj.name}' 메시의 '{mat_slot.material.name}' 매테리얼에\n{filepath} 텍스쳐 파일이 실제로 존재하지 않습니다.\n매테리얼에 지정되어 있는 텍스쳐 경로가 올바른지, 실제로 텍스쳐가 경로 내에 존재하는지 확인하세요."
                                    show_info_message(error_message)
                                    raise FileNotFoundError(error_message)
                                images[filepath] = image
    return images

# each 모드 텍스쳐 크기 제한
def resize_if_exceeds(image, max_size):
    width, height = image.size
    if width > max_size or height > max_size:
        ratio = min(max_size / width, max_size / height)
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, Image.LANCZOS)
    return image

# each 모드
def rectpack(images, max_texture_size):
    try:
        img_files = list(images.keys())
        image_objects = [Image.open(f) for f in img_files]

        image_objects = [resize_if_exceeds(img, max_texture_size) for img in image_objects]

        rectangles = [img.size for img in image_objects]
        total_area = sum(w * h for w, h in rectangles)

        packer = newPacker(bin_algo=PackingBin.BBF, pack_algo=MaxRectsBlsf, sort_algo=SORT_LSIDE, rotation=False)

        for i, img in enumerate(image_objects):
            packer.add_rect(*img.size, img_files[i])

        width = height = int(math.sqrt(total_area))

        width = 1024 * math.ceil(width / 1024)
        height = 1024 * math.ceil(height / 1024)

        if width * height < total_area:
            width = 1024 * math.ceil(total_area / height / 1024)
        else:
            height = 1024 * math.ceil(total_area / width / 1024)

        packer.add_bin(width, height)
        packer.pack()

        all_rects = packer.rect_list()

        max_right = max(x + w for b, x, y, w, h, rid in all_rects)
        max_bottom = max(y + h for b, x, y, w, h, rid in all_rects)

        total_width = math.ceil(max_right / 1024) * 1024
        total_height = math.ceil(max_bottom / 1024) * 1024

        result = Image.new("RGBA", (total_width, total_height))

        image_positions = {}
        for bID, x, y, w, h, rid in packer.rect_list():
            filepath = rid
            img_index = img_files.index(filepath)
            img = image_objects[img_index]
            result.paste(img, (x, y))
            image_positions[filepath] = (x, y, w, h)

        return result, image_positions, total_width, total_height
    except Exception as e:
        print("rectpack error")
        print(str(e))
        #print("Traceback:")
        #print(traceback.format_exc())

# atlas 모드 텍스쳐 크기 조절
def resize_images_atlasmode(images, target_width, target_height):
    resized_images = []
    for img in images:
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height

        if img_ratio > target_ratio:
            new_width = target_width
            new_height = int(new_width / img_ratio)
        else:
            new_height = target_height
            new_width = int(new_height * img_ratio)

        resized_images.append(img.resize((new_width, new_height), Image.LANCZOS))

    return resized_images

# atlas 모드
def rectpack_atlas(images, max_texture_size):
    try:
        img_files = list(images.keys())
        image_objects = [Image.open(f) for f in img_files]

        total_width = total_height = max_texture_size

        image_objects = resize_images_atlasmode(image_objects, total_width, total_height)

        packer = newPacker(bin_algo=PackingBin.BBF, pack_algo=MaxRectsBlsf, sort_algo=SORT_LSIDE, rotation=False)

        for img, filepath in zip(image_objects, img_files):
            packer.add_rect(*img.size, filepath)

        packer.add_bin(total_width, total_height)
        packer.pack()

        result = Image.new("RGBA", (total_width, total_height))

        image_positions = {}
        for bID, x, y, w, h, rid in packer.rect_list():
            filepath = rid
            img_index = img_files.index(filepath)
            img = image_objects[img_index]
            result.paste(img, (x, y))
            image_positions[filepath] = (x, y, w, h)

        return result, image_positions, total_width, total_height
    except Exception as e:
        print("rectpack_atlas error")
        print(str(e))
        #print("Traceback:")
        #print(traceback.format_exc())

# uv 매핑
def update_uv_map(obj, img, uv_info, canvas_size):
    try:
        uv_layer = obj.data.uv_layers.active.data

        img_filepath = bpy.path.abspath(img.filepath)

        img_x, img_y, img_width, img_height = uv_info[img_filepath]
        canvas_width, canvas_height = canvas_size

        for poly in obj.data.polygons:
            for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                loop = obj.data.loops[loop_index]
                uv = uv_layer[loop.index].uv

                new_x = (uv.x * img_width / canvas_width) + (img_x / canvas_width)
                new_y = 1 - (((1 - uv.y) * img_height / canvas_height) + (img_y / canvas_height))

                uv.x = new_x
                uv.y = new_y
    except Exception as e:
        show_info_message(f"UV 맵 업데이트 중 오류 발생: {str(e)}")

def get_base_name(mesh_name):
    return re.sub(r'\.\d+$', '', mesh_name)

def set_material_to_mesh(obj, image_filepath):
    if not obj.data.materials:
        mat = bpy.data.materials.new(name="MergedMaterial")
        obj.data.materials.append(mat)
    else:
        mat = obj.data.materials[0]
    
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    for node in nodes:
        nodes.remove(node)
    
    bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf_node.location = (0, 0)

    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.location = (-300, 0)
    tex_image = bpy.data.images.load(image_filepath)
    tex_node.image = tex_image

    links.new(tex_node.outputs['Color'], bsdf_node.inputs['Base Color'])
    
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (200, 0)
    links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    mat.node_tree.nodes.active = bsdf_node

# main
def uv_map_merge(output_filepath, skip_matcap, skip_toon_texture, full_auto_uvmap, alpha_invert, max_texture_size=1024, link_materials=True, max_texture_mode="each"):
    try:
        selected_objects = bpy.context.selected_objects

        created_textures = {}
        merged_textures_by_mesh_name = {}

        result_image = None
        image_positions = {}
        canvas_width = 0
        canvas_height = 0

        if full_auto_uvmap:
            grouped_objects = group_objects_by_name(selected_objects)
            for mesh_name, objects in grouped_objects.items():
                selected_images = get_selected_meshes_images(objects, skip_matcap, skip_toon_texture)
                if not selected_images:
                    error_message = f"{mesh_name}의 그룹에서 텍스쳐를 찾을 수 없습니다."
                    show_info_message(error_message)
                    return

                print(f"{mesh_name}에 대해 병합할 텍스쳐 {len(selected_images)}개를 찾았습니다.")

                if max_texture_mode == "each":
                    result_image, image_positions, canvas_width, canvas_height = rectpack(selected_images, max_texture_size)
                elif max_texture_mode == "atlas":
                    result_image, image_positions, canvas_width, canvas_height = rectpack_atlas(selected_images, max_texture_size)
                else:
                    raise ValueError("Choose 'each' or 'atlas'")    

                if not result_image:
                    error_message = f"{mesh_name}에 대한 텍스쳐 병합에 실패했습니다. 텍스쳐가 유효하고 접근 가능한지 확인하세요."
                    show_info_message(error_message)
                    return

                print(f"{mesh_name}에 대한 텍스쳐 병합 완료, UV 맵 업데이트 중...")

                updated_objects = 0
                for obj in objects:
                    for mat_slot in obj.material_slots:
                        if mat_slot.material and mat_slot.material.use_nodes:
                            for node in mat_slot.material.node_tree.nodes:
                                if node.type == 'TEX_IMAGE':
                                    image = node.image
                                    if image and image.filepath in image_positions:
                                        update_uv_map(obj, image, image_positions, (canvas_width, canvas_height))
                                        updated_objects += 1

                if not updated_objects:
                    error_message = f"{mesh_name}에 대한 UV 맵이 업데이트되지 않았습니다. 선택한 객체에 UV 맵이 있는지 확인하세요."
                    show_info_message(error_message)
                    continue

                print(f"{mesh_name}에 대해 {updated_objects}개의 객체가 업데이트되었습니다.")

                base_name = get_base_name(mesh_name)
                
                if base_name in created_textures:
                    merged_texture_path = created_textures[base_name]
                else:
                    merged_texture_path = save_texture(result_image, output_filepath, base_name, alpha_invert)
                    created_textures[base_name] = merged_texture_path

        else:
            selected_images = get_selected_meshes_images(selected_objects, skip_matcap, skip_toon_texture)
            if not selected_images:
                show_info_message("선택한 메쉬에서 텍스쳐를 찾을 수 없습니다. 메쉬 객체를 선택하세요.")
                return

            print(f"병합할 텍스쳐 {len(selected_images)}개를 찾았습니다.")

            if max_texture_mode == "each":
                result_image, image_positions, canvas_width, canvas_height = rectpack(selected_images, max_texture_size)
            elif max_texture_mode == "atlas":
                result_image, image_positions, canvas_width, canvas_height = rectpack_atlas(selected_images, max_texture_size)
            if not result_image:
                error_message = "텍스쳐 병합에 실패했습니다. 텍스쳐가 유효하고 접근 가능한지 확인하세요."
                show_info_message(error_message)
                return

            print("텍스쳐 병합 완료, UV 맵 업데이트 중...")

            updated_objects = 0
            for obj in selected_objects:
                if obj.type == 'MESH':
                    for mat_slot in obj.material_slots:
                        if mat_slot.material and mat_slot.material.use_nodes:
                            for node in mat_slot.material.node_tree.nodes:
                                if node.type == 'TEX_IMAGE':
                                    image = node.image
                                    img_filepath = bpy.path.abspath(image.filepath)
                                    if image and img_filepath in image_positions:
                                        update_uv_map(obj, image, image_positions, (canvas_width, canvas_height))
                                        updated_objects += 1

            if not updated_objects:
                error_message = "UV 맵이 업데이트되지 않았습니다. 선택한 객체에 UV 맵이 있는지 확인하세요."
                show_info_message(error_message)
                return

            print(f"{updated_objects}개의 매쉬가 정상적으로 패킹되었습니다.")
            show_info_message(f"{updated_objects}개의 매쉬가 정상적으로 패킹되었습니다.")

            # save_texture(result_image, output_filepath, "", alpha_invert)
            merged_texture_path = save_texture(result_image, output_filepath, "", alpha_invert)

            if link_materials and not full_auto_uvmap:
                merged_texture_path = save_texture(result_image, output_filepath, "", alpha_invert)
                for obj in selected_objects:
                    if obj.type == 'MESH':
                        set_material_to_mesh(obj, merged_texture_path)

        if link_materials:
            for obj in selected_objects:
                if obj.type == 'MESH':
                    base_name = get_base_name(obj.name)
                    if base_name in created_textures:
                        merged_texture_path = created_textures[base_name]
                        set_material_to_mesh(obj, merged_texture_path)

    except FileNotFoundError:
        return

    except Exception as e:
        show_info_message(f"오류가 발생했습니다: {str(e)}")
        print("\nTraceback:")
        print(traceback.format_exc())
