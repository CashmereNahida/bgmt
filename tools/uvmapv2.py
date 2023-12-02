import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty
import os
from PIL import Image, ImageOps
from math import ceil
import subprocess
import sys
import traceback

# error
def show_error_message(message):
    print(message)
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title="Error", icon='ERROR')

# 텍스쳐 저장
def save_texture(image, output_filepath, mesh_name, alpha_invert):
    try:
        if mesh_name:
            base_name, extension = os.path.splitext(output_filepath)
            file_name = f"{base_name}{mesh_name.capitalize()}Diffuse{extension}"
        else:
            file_name = output_filepath

        if alpha_invert:
            r, g, b, a = image.split()
            a = a.point(lambda p: 255 - p)
            image = Image.merge("RGBA", (r, g, b, a))

        image_filepath = bpy.path.abspath(file_name)

        image.save(image_filepath)
        print(f"병합된 텍스쳐가 {image_filepath}에 저장되었습니다.")
    except Exception as e:
        error_message = str(e)
        if "unknown file extension" in error_message:
            show_error_message("정상적이지 않은 파일 확장자입니다.")
        else:
            show_error_message(f"텍스쳐 저장 중 오류 발생: {error_message}")

def group_objects_by_name(objects):
    groups = {}
    for obj in objects:
        base_name = obj.name.split(".")[0]
        if base_name not in groups:
            groups[base_name] = []
        groups[base_name].append(obj)
    return groups

# 메쉬에서 텍스쳐 이미지 추출
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
                                images[filepath] = image
    return images

# 텍스쳐 이미지 병합
def merge_images_into_one(images, max_texture_size):
    try:
        current_x = 0
        current_y = 0
        max_row_height = 0

        total_images = len(images)

        side_length = max_texture_size * ceil(total_images**0.5)

        temp_canvas = Image.new('RGBA', (side_length, side_length), (0, 0, 0, 0))
        
        print(f"초기 side_length: {side_length}, 총 이미지 수: {total_images}")

        image_positions = {}

        for key, img in images.items():
            try:
                image_path = bpy.path.abspath(img.filepath)
                texture_image = Image.open(image_path).convert("RGBA")

                print(f"이미지 처리 중: {image_path}, 크기: {texture_image.size}")

                if texture_image.width > max_texture_size or texture_image.height > max_texture_size:
                    texture_image.thumbnail((max_texture_size, max_texture_size))
                    print(f"이미지 크기 조정: {texture_image.size}")

                if current_x + texture_image.width > temp_canvas.width:
                    current_x = 0
                    current_y += max_row_height
                    max_row_height = 0

                print(f"이미지 위치: {current_x}, {current_y}")

                image_positions[img.filepath] = (current_x, current_y, texture_image.width, texture_image.height)

                temp_canvas.paste(texture_image, (current_x, current_y))
                current_x += texture_image.width
                max_row_height = max(max_row_height, texture_image.height)

            except Exception as e:
                show_error_message(f"{img.filepath} 처리 중 오류 발생: {str(e)}")

        used_box = temp_canvas.getbbox()

        new_width = ceil(used_box[2] / max_texture_size) * max_texture_size
        new_height = ceil(used_box[3] / max_texture_size) * max_texture_size

        print(f"새 캔버스 크기: {new_width}x{new_height}, 사용된 영역: {used_box}")

        result_canvas = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        result_canvas.paste(temp_canvas, (0, 0))

        return result_canvas, image_positions, new_width, new_height
    except Exception as e:
        show_error_message(f"이미지 병합 중 오류 발생: {str(e)}")
        print(str(e))
        print("\nTraceback:")
        print(traceback.format_exc())

        return None, None, 0, 0

# uv 매핑
def update_uv_map(obj, img, uv_info, canvas_size):
    try:
        uv_layer = obj.data.uv_layers.active.data

        img_x, img_y, img_width, img_height = uv_info[img.filepath]
        canvas_width, canvas_height = canvas_size

        for poly in obj.data.polygons:
            for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                loop = obj.data.loops[loop_index]
                uv = uv_layer[loop.index].uv

                new_x = (uv.x * img_width + img_x) / canvas_width
                new_y = 1 - ((1 - uv.y) * img_height + img_y) / canvas_height

                uv.x = new_x
                uv.y = new_y
    except Exception as e:
        show_error_message(f"UV 맵 업데이트 중 오류 발생: {str(e)}")

# main
def uv_map_merge(max_texture_size, output_filepath, skip_matcap, skip_toon_texture, full_auto_uvmap, alpha_invert):
    try:
        selected_objects = bpy.context.selected_objects

        if full_auto_uvmap:
            grouped_objects = group_objects_by_name(selected_objects)

            for mesh_name, objects in grouped_objects.items():
                selected_images = get_selected_meshes_images(objects, skip_matcap, skip_toon_texture)
                if not selected_images:
                    error_message = f"{mesh_name}의 그룹에서 이미지를 찾을 수 없습니다. 건너뜁니다..."
                    show_error_message(error_message)
                    continue

                print(f"{mesh_name}에 대해 병합할 이미지 {len(selected_images)}개를 찾았습니다.")

                result_image, image_positions, canvas_width, canvas_height = merge_images_into_one(selected_images, max_texture_size)
                if not result_image:
                    error_message = f"{mesh_name}에 대한 이미지 병합에 실패했습니다. 이미지가 유효하고 접근 가능한지 확인하세요."
                    show_error_message(error_message)
                    continue

                print(f"{mesh_name}에 대한 이미지 병합 완료, UV 맵 업데이트 중...")

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
                    show_error_message(error_message)
                    continue

                print(f"{mesh_name}에 대해 {updated_objects}개의 객체가 업데이트되었습니다.")

                save_texture(result_image, output_filepath, mesh_name, alpha_invert)

        else:
            selected_images = get_selected_meshes_images(selected_objects, skip_matcap, skip_toon_texture)
            if not selected_images:
                error_message = "선택한 메쉬에서 이미지를 찾을 수 없습니다. 메쉬 객체를 선택하세요."
                show_error_message(error_message)
                return

            print(f"병합할 이미지 {len(selected_images)}개를 찾았습니다.")

            result_image, image_positions, canvas_width, canvas_height = merge_images_into_one(selected_images, max_texture_size)
            if not result_image:
                error_message = "이미지 병합에 실패했습니다. 이미지가 유효하고 접근 가능한지 확인하세요."
                show_error_message(error_message)
                print(str(e))
                print("\nTraceback:")
                print(traceback.format_exc())
                return

            print("이미지 병합 완료, UV 맵 업데이트 중...")

            updated_objects = 0
            for obj in selected_objects:
                if obj.type == 'MESH':
                    for mat_slot in obj.material_slots:
                        if mat_slot.material and mat_slot.material.use_nodes:
                            for node in mat_slot.material.node_tree.nodes:
                                if node.type == 'TEX_IMAGE':
                                    image = node.image
                                    if image and image.filepath in image_positions:
                                        update_uv_map(obj, image, image_positions, (canvas_width, canvas_height))
                                        updated_objects += 1

            if not updated_objects:
                error_message = "UV 맵이 업데이트되지 않았습니다. 선택한 객체에 UV 맵이 있는지 확인하세요."
                show_error_message(error_message)
                return

            print(f"{updated_objects}개의 객체가 업데이트되었습니다.")

            save_texture(result_image, output_filepath, "", alpha_invert)

    except Exception as e:
        show_error_message(f"오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    max_texture_size = 1024
    output_filepath = "//custom_texture_location.png"
    skip_matcap = True
    skip_toon_texture = True
    full_auto_uvmap = False
    alpha_invert = False
    uv_map_merge(max_texture_size, output_filepath, skip_matcap, skip_toon_texture, full_auto_uvmap, alpha_invert)
