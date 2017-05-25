import json
import maya.cmds as cmds
import maya.mel as mel

from Qt import QtWidgets, QtCore
from Tools37.Maya import cute_utils as cu
from Tools37.cute.widgets import Widget37
from mocap_model import MocapModel


def start_instance():
    widget = VertexSelectorWindow(parent=cu.get_maya_main_window())
    widget.show()


class VertexSelectorWindow(QtWidgets.QWidget):
    _TITLE = "Mocap Vertex Selector"
    _WIDTH = 400
    _WILD_CARD = " "

    def __init__(self, parent=None):
        super(VertexSelectorWindow, self).__init__(parent)
        self._table_view = None
        self._table_model = None
        self._combox = None
        self._init_dialog()

    def _init_dialog(self):
        self.setWindowTitle(self._TITLE)
        self.setFixedWidth(self._WIDTH)

        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)

        self._table_model = MocapModel()
        self._table_view = QtWidgets.QTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._table_view.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self._table_view.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)
        for i in range(self._table_view.horizontalHeader().count()):
            self._table_view.horizontalHeader().setSectionResizeMode(
                i, QtWidgets.QHeaderView.Stretch)

        main_layout.addWidget(self._table_view)

        button = QtWidgets.QPushButton("Add Vertex")
        button.clicked.connect(self._add_row)
        main_layout.addWidget(button)

        button = QtWidgets.QPushButton("Set Vertex")
        button.clicked.connect(self._set_vertex)
        main_layout.addWidget(button)

        button = QtWidgets.QPushButton("Delete Row")
        button.clicked.connect(self._delete_row)
        main_layout.addWidget(button)

        space = QtWidgets.QSpacerItem(
            32, 32, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        main_layout.addItem(space)

        button = QtWidgets.QPushButton("Import")
        button.clicked.connect(self._import)
        main_layout.addWidget(button)

        button = QtWidgets.QPushButton("Export")
        button.clicked.connect(self._export)
        main_layout.addWidget(button)

        space = QtWidgets.QSpacerItem(
            32, 32, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        main_layout.addItem(space)

        self._combox = QtWidgets.QComboBox()
        self._combox.addItem(self._WILD_CARD)
        main_layout.addWidget(self._combox)

        button = QtWidgets.QPushButton("Set Mocap")
        button.clicked.connect(self._set_mocap)
        main_layout.addWidget(button)

        button = QtWidgets.QPushButton("Load Mocap")
        button.clicked.connect(self._load_controllers)
        main_layout.addWidget(button)

        button = QtWidgets.QPushButton("Populate Mocap")
        button.clicked.connect(self._populate_mocap)
        main_layout.addWidget(button)

    # Data stuff #

    def _add_row(self):
        mocap = self._combox.currentText()
        succes = self._table_model.add(mocap, self._WILD_CARD)

        if succes:
            index = self._combox.currentIndex()
            if not index == 0 or index < 0:
                self._combox.removeItem(index)
                self._combox.setCurrentIndex(0)

    def _set_vertex(self):
        row = self._table_view.currentIndex().row()
        self._table_model.set_vertex(row)

    def _delete_row(self):
        row = self._table_view.currentIndex().row()
        self._table_model.remove(row)

    def _import(self):
        try:
            title = "Choose file to import"
            file_metadata = QtWidgets.QFileDialog.getOpenFileName(
                self, title, dir=".", filter="(*.json)")
            file_name = file_metadata[0]
        except IOError:
            print "IOError occurred, please try again."
            return None

        if len(file_name) < 3:
            print "Filename too short."
            return None

        with open(file_name, 'r') as the_file:
            data = json.load(the_file)

        for key in sorted(data.keys()):
            self._table_model.add_row(
                key, [data[key]["object"], data[key]["vertexInd"]])

    def _export(self):
        if not self._table_model.can_export_json():
            message = "Not all mocap values are unique, ensure they are all unique."
            reply = QtWidgets.QMessageBox.information(
                self, 'Export Error', message, QtWidgets.QMessageBox.Ok)
            return

        try:
            title = "Choose file to export to"
            file_metadata = QtWidgets.QFileDialog.getSaveFileName(
                self, title, dir=".", filter="(*.json)")
            file_name = file_metadata[0]
        except IOError:
            print "IOError occurred, please try again."
            return

        if len(file_name) < 3:
            return

        data = self._table_model.get_json()
        with open(file_name, 'w') as the_file:
            json.dump(data, the_file, sort_keys=True,
                      indent=4, separators=(',', ': '))

    def _set_mocap(self):
        row = self._table_view.currentIndex().row()
        if not row < 0:
            self._table_model.set_mocap(
                row, self._combox.currentText(), self._WILD_CARD)
            index = self._combox.currentIndex()
            if not index == 0 or index < 0:
                self._combox.removeItem(index)
                self._combox.setCurrentIndex(0)

    def _load_controllers(self):
        controllers = self._load_controller_file()
        if controllers is None:
            return

        controllers = [
            x for x in controllers if x not in self._table_model.get_mocap_list()]
        controllers = sorted(controllers)
        self._combox.clear()
        self._combox.addItem(self._WILD_CARD)
        self._combox.addItems(controllers)

    def _load_controller_file(self):
        try:
            file_metadata = QtWidgets.QFileDialog.getOpenFileName(
                self, "Choose file", dir=".", filter="(*.json)")
            file_name = file_metadata[0]
        except IOError:
            print "IOError occurred, please try again."
            return None

        if len(file_name) < 3:
            print "Filename too short."
            return None

        with open(file_name, 'r') as the_file:
            data = json.load(the_file)
            if isinstance(data, dict):
                controllers = data.get("mocap_trackers", None)
                if controllers is not None and isinstance(controllers, dict):
                    return controllers.keys()

        print "Cannot properly parse file."
        return None

    def _populate_mocap(self):
        controllers = self._load_controller_file()
        if controllers is None:
            return

        controllers = [
            x for x in controllers if x not in self._table_model.get_mocap_list()]
        controllers = sorted(controllers)
        self._table_model.populate_mocap(controllers)

    def _on_selection_changed(self):
        row = self._table_view.currentIndex().row()
        self._table_model.highlight(row)

    def closeEvent(self, event):
        global _INSTANCE
        _INSTANCE = None
        self._table_model.delete()
        return super(VertexSelectorWindow, self).closeEvent(event)
