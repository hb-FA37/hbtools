import os
import json
import maya.cmds as cmds
import maya.mel as mel

from Tools37.maya.olm.olm_view import OlmWidget
from Qt import QtWidgets, QtCore


class OlmController(OlmWidget):
    def __init__(self, parent=None):
        super(OlmController, self).__init__(parent)
        self._blendshape = None
        self._output_geometry = None
        self._init_mel()
        self._connect_signals()

    def _init_mel(self):
        mel.eval('if(!`exists doMenuComponentSelection`) eval("source dagMenuProc")')

    def _connect_signals(self):
        self.signal_refresh_blendshape.connect(self._reload_blendshapes)
        self.signal_set_blendshape.connect(self._set_blendshape)

        self.signal_selection_mode.connect(self._enter_vertex_selection)
        self.signal_add_row.connect(self._add_row)
        self.signal_remove_row.connect(self._delete_row)

        self.signal_import_selection.connect(self._import)
        self.signal_export_selection.connect(self._export)

        self.signal_vertex_sphere_size.connect(self._table_model.resize_vertex_spheres)
        self.signal_control_sphere_size.connect(self._table_model.resize_control_spheres)

    # Blendshape #

    def _set_blendshape(self):
        self._blendshape = self._blendshape_combox.currentText()
        self._output_geometry = cmds.listConnections("{}.outputGeometry[0]".format(self._blendshape), source=False, destination=True)[0]
        self._table_model.set_scene_objects(self._blendshape, self._output_geometry)
        self._blendshape_combox.setEnabled(False)
        self._set_button.setEnabled(False)

    @classmethod
    def _get_blendshapes(cls):
        return [str(b) for b in cmds.ls(type='blendShape')]

    def _reload_blendshapes(self):
        if not self._blendshape_combox.isEnabled():
            return
        self._blendshape_combox.clear()
        self._blendshape_combox.addItems(self._get_blendshapes())

    # Vertex #

    def _enter_vertex_selection(self):
        if self._blendshape is None:
            print "No blendshape set yet."
            return

        try:
            mel.eval('doMenuComponentSelection("{}", "vertex")'.format(self._output_geometry))
        except RuntimeError, error:
            print error

    def _add_row(self):
        vertex_data = self._get_selected_vertex()
        if vertex_data is None:
            print "Didn't select a vertex"
            return
        if vertex_data[0] != self._output_geometry:
            print "Selected vertex not of {}".format(self._output_geometry)
            return

        self._table_model.add(vertex_data[1])

    def _delete_row(self):
        row = self._table_view.currentIndex().row()
        self._table_model.remove(row)

    def _get_selected_vertex(self):
        vertex_data = cmds.ls(selection=True, showType=True)
        if len(vertex_data) != 2:
            print "Selected too much, only select a singular vertex."
            return None
        if vertex_data[1] != "float3":
            print "Did not select a vertex."
            return None

        vtx_data = vertex_data[0].rsplit(".", 2)  # mesh
        if not vtx_data[1].startswith("vtx"):
            print "Vertex Error."
            return None

        vtx_data[1] = vtx_data[1][3:]
        vtx_data[1] = vtx_data[1][1:-1]  # Index number
        return vtx_data  # [mesh, vtx index]

    # Import / Export #

    def _import(self):
        try:
            title = "Choose import file"
            file_metadata = QtWidgets.QFileDialog.getOpenFileName(self, title, dir=".", filter="(*.json)")
            file_name = file_metadata[0]
        except IOError:
            print "IOError occurred, please try again."
            return None

        if len(file_name) < 2:
            print "Filename too short."
            return None

        with open(file_name, 'r') as the_file:
            data = json.load(the_file)
            self._import_update_blendshape(data["blendshape"])
            self._table_model.load_json(data)

    def _import_update_blendshape(self, blendshape):
        # TODO; Refactor, not clean.
        self._blendshape_combox.clear()
        self._blendshape_combox.addItem(blendshape)
        self._blendshape_combox.setCurrentIndex(0)
        self._blendshape_combox.setEnabled(False)
        self._set_button.setEnabled(False)

    def _export(self):
        try:
            title = "Choose file to export to"
            file_metadata = QtWidgets.QFileDialog.getSaveFileName(self, title, dir=".", filter="(*.json)")
            file_name = file_metadata[0]
        except IOError:
            print "IOError occurred, please try again."
            return

        if len(file_name) < 3:
            return

        data = self._table_model.get_json()
        with open(file_name, 'w') as the_file:
            json.dump(data, the_file, sort_keys=True, indent=4, separators=(',', ': '))
