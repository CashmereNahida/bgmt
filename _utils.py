import bpy



def addon_preferences(attrname, default=None):
    if hasattr(bpy.context, 'preferences'):
        addon = bpy.context.preferences.addons.get(__package__, None)
    else:
        addon = bpy.context.user_preferences.addons.get(__package__, None)
    return getattr(addon.preferences, attrname, default) if addon else default



def show_info_message(message):
    print(message)
    message_lines = message.split('\n')
    def draw(self, context):
        for line in message_lines:
            self.layout.label(text=line)
    bpy.context.window_manager.popup_menu(draw, title="Info", icon='INFO')



import sys
import subprocess
from os.path import dirname, join, normpath

def start_install_packages(packages):
    blender_path = dirname(sys.executable)
    python_path = normpath(join(blender_path, '..', 'bin', 'python.exe'))

    for package in packages:
        try:
            subprocess.check_call([python_path, "-m", "pip", "install", package])
            print(f"라이브러리 설치 성공: {package}")
        except Exception as e:
            print(f"라이브러리 설치 실패: {package} - {e}")

class UIInstallModules(bpy.types.Operator):
    bl_idname = "start.install_modules"
    bl_label = "설치"

    def execute(self, context):
        try:
            from bgmt import PackageStatus
        except ModuleNotFoundError:
            from blender_genshin_mod_tools import PackageStatus
            status = PackageStatus.get_instance()
            packages = status.packages
            start_install_packages(packages)
            show_info_message("정상적으로 설치되었습니다.")
            status.installed_packages = True
        except Exception:
            show_info_message("모듈 설치 실패. 블렌더를 관리자 권한으로 실행한 후 다시 시도하세요")