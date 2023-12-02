import bpy
import sys
import subprocess
from os.path import dirname, join, normpath
from .._utils import show_info_message

installed_modules = {}

def start_install_packages(python_path, package):
    try:
        subprocess.check_call([python_path, "-m", "pip", "install", package])
        installed_modules[package] = True
        print(f"{package} 패키지가 설치되었습니다.")
    except Exception as e:
        installed_modules[package] = False
        message=f"{package} 패키지 설치 중 오류가 발생했습니다: {e}"
        show_info_message(message)

def check_and_install_packages():
    blender_path = dirname(sys.executable)
    python_path = normpath(join(blender_path, '..', 'bin', 'python.exe'))
    
    required_packages = ["pillow", "rectpack"]
    try:
        installed_packages_output = subprocess.check_output([python_path, "-m", "pip", "list"]).decode("utf-8")
        installed_packages = {line.split()[0].lower(): line.split()[1] for line in installed_packages_output.splitlines() if " " in line}
    except Exception as e:
        message="설치된 패키지를 확인하는 중 오류가 발생했습니다: {e}"
        show_info_message(message)
        return

    for package in required_packages:
        if package.lower() not in installed_packages:
            start_install_packages(python_path, package)
        else:
            installed_modules[package] = True
            # print(f"{package} 패키지가 이미 설치되어 있습니다.")

class OBJECT_OT_InstallRequiredModules(bpy.types.Operator):
    bl_idname = "object.install_required_modules"
    bl_label = "필수 모듈 설치 확인"
    bl_description = "Pillow와 Rectpack 설치"

    def execute(self, context):
        check_and_install_packages()
        return {'FINISHED'}

classes = (
    OBJECT_OT_InstallRequiredModules,
)


def register():

    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    
    for c in classes:
        bpy.utils.unregister_class(c)