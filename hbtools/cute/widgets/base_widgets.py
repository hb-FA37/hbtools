"""
Basic widgets that have some setup
"""

from Qt import QtWidgets, QtCore
from slider_widget import *
from accordion_widget import *


class MayaWidgetHB(QtWidgets.QWidget):
    def __init__(self, center=True, parent=None):
        super(MayaWidgetHB, self).__init__(parent=parent)
        self._init_widget()
        if center:
            self._center_in_parent()

    def _init_widget(self):
        self._delete_existing()
        self.setObjectName(self._get_object_name())
        self.setWindowTitle(self._get_window_title())

    def _get_object_name(self):
        raise NotImplementedError()

    def _get_window_title(self):
        raise NotImplementedError()

    def _center_in_parent(self):
        if self.parent() is None:
            return

        parent_pos = self.parent().pos()
        parent_width = self.parent().width()
        parent_height = self.parent().height()

        parent_center_x = parent_pos.x() + parent_width / 2
        parent_center_y = parent_pos.y() + parent_height / 2

        self.move(QtCore.QPoint(parent_center_x - self.width() / 2,
                                parent_center_y - self.height() / 2))

    def _delete_existing(self):
        import maya.cmds as cmds
        if cmds.window(self._get_object_name, exists=True):
            cmds.deleteUI(self._get_object_name, wnd=True)
