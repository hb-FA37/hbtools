from Tools37.Maya.animation.olm_controller import OlmController
from Tools37.Maya.cute_utils import get_maya_main_window
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class OlmMixinController(MayaQWidgetDockableMixin, OlmController):
    """ MayaMixin wrapper around the main view, allows it to be dockable.
    We use the 2016v2 version as the 2017 version works with workspace controls which breaks alot of
    qt signals and has some issues in my opinion. For example, you cannot intercept the closeEvent anymore.
    Will be removed once they fix Mixin2017 or when I understand it better.
    """
    pass


def show_tool():
    parent = get_maya_main_window()
    view = OlmController(parent=parent)
    view.show()


def show_mixin_tool():
    parent = get_maya_main_window()
    view = OlmMixinController(parent=parent)
    view.show(dockable=True)
