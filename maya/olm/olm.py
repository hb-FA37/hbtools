from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from Tools37.maya.olm.olm_controller import OlmController
from Tools37.maya.cute_utils import get_maya_main_window


class OlmMixinController(MayaQWidgetDockableMixin, OlmController):
    """ MayaMixin wrapper around the main view, allows it to be dockable. """
    pass


def show_tool():
    parent = get_maya_main_window()
    view = OlmController(parent=parent)
    view.show()


def show_mixin_tool():
    parent = get_maya_main_window()
    view = OlmMixinController(parent=parent)
    view.show(dockable=True)
