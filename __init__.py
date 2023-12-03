bl_info = \
    {
        "name": "Genshin Mod Tools",
        "author": "CashmereNahida",
        "version": (0, 1, 1),
        "blender": (3, 6, 5),
        "location": "View3D > Sidebar > Genshin Mod Tools",
        "description": "모드 제작시 자주쓰는 기능 모음",
        "warning": "",
        "wiki_url" : "",
        "tracker_url" : "",
        "doc_url": "",
        "category": "Interface",
    }



# based on SilentNightSound, leotorrez, kusaknee



import bpy
from bpy.utils import register_class, unregister_class



class PackageStatus:
    _instance = None

    @staticmethod
    def get_instance():
        if PackageStatus._instance is None:
            PackageStatus._instance = PackageStatus()
        return PackageStatus._instance

    def __init__(self):
        if PackageStatus._instance is not None:
            raise Exception("This class is a singleton!")
        self.installed_packages = False
        self.packages = ["pillow", "rectpack"]


status = PackageStatus.get_instance()
try:
    import rectpack, PIL
    status.installed_packages = True
except ImportError:
    try:
        from ._utils import start_install_packages
        start_install_packages(status.packages)
        status.installed_packages = True
    except Exception as e:
        status.installed_packages = False


def info_msg(self, context):
    self.layout.label(text="Blender 3DMigoto GIMI 애드온이 설치되지 않았습니다. 먼저 해당 애드온을 설치 후 시도하세요.")
try:
    from blender_3dmigoto_gimi import export_3dmigoto_genshin, Fatal, Import3DMigotoFrameAnalysis, import_3dmigoto
except ImportError:
    bpy.context.window_manager.popup_menu(info_msg, title="Info", icon='INFO')






from . import addon_updater_ops


from . import _ui, _properties
from .operator import _color_attribute, _import_export, _finalcheck, _usefultools, _uvmap, _vertex
from .tools import vg_remap, vg_manual







@addon_updater_ops.make_annotations
class Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    auto_check_update = bpy.props.BoolProperty(
		name="Auto-check for Update",
		description="If enabled, auto-check for updates using an interval",
		default=False)

    updater_interval_months = bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0)

    updater_interval_days = bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31)

    updater_interval_hours = bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23)

    updater_interval_minutes = bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59)
     
################################################################################################################
################################################################################################################
################################################################################################################
################################################################################################################
################################################################################################################
################################################################################################################

    set_advanced_settings: bpy.props.BoolProperty(
        name="Advanced Settings",
        description="고급 설정",
        default=False,
    )

    enable_final_check: bpy.props.BoolProperty(
        name="Final Check 활성화",
        description="Final Check를 활성화 합니다",
        default=True,
    )

    basebody_file_path: bpy.props.StringProperty(
        name="Base Body File Path",
        subtype='FILE_PATH',
    )

    """
    def draw(self, context):

        _ui.Settings.draw(self, context)
    """













modules = [
    #.
    _properties,
    _ui,

    #operator
    _color_attribute,
    _import_export,
    _finalcheck,
    _usefultools,
    _uvmap,
    _vertex,

    #tools
    vg_remap,
    vg_manual,
]



classes = (
    Preferences,
)

def register():

    for module in modules:
        module.register()

    bpy.types.Scene.Head = bpy.props.PointerProperty(type=bpy.types.Collection)
    bpy.types.Scene.Body = bpy.props.PointerProperty(type=bpy.types.Collection)
    bpy.types.Scene.Dress = bpy.props.PointerProperty(type=bpy.types.Collection)
    bpy.types.Scene.Extra = bpy.props.PointerProperty(type=bpy.types.Collection)

    for cls in classes:
        register_class(cls) 

    addon_updater_ops.register(bl_info)
    
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=_properties.MyProperties)  

def unregister():

    for module in modules:
        module.unregister()

    del bpy.types.Scene.Extra
    del bpy.types.Scene.Dress
    del bpy.types.Scene.Body
    del bpy.types.Scene.Head

    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()