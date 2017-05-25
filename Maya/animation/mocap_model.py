from Qt import QtCore
import collections
import maya.cmds as cmds
import maya.mel as mel


class MocapModel(QtCore.QAbstractTableModel):
    _SPHERE_DEF_SIZE = 0.1
    _MODEL_KEY = "object"
    _VERTEX_KEY = "vertexInd"

    def __init__(self, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._headers = ["Tracker", "Vertex"]
        self._mocap_list = []
        self._vertex_list = []
        self._sphere_list = []
        self._shader_node = None
        self._selected_shader_node = None
        self._setup_sphere_shader()

    def delete(self):
        try:
            cmds.delete(self._shader_node)
        except RuntimeError:
            pass

        try:
            cmds.delete(self._selected_shader_node)
        except RuntimeError:
            pass

        for sphere in self._sphere_list:
            if sphere is not None:
                try:
                    cmds.delete(sphere)
                except RuntimeError:
                    pass

    # IMPLEMENT
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._mocap_list)

    # IMPLEMENT
    def columnCount(self, parent=QtCore.QModelIndex()):
        return 2

    # IMPLEMENT
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                i = index.row()
                j = index.column()
                if j == 0:
                    return self._mocap_list[i]
                return self._vertex_list[i][1] + " - " + self._vertex_list[i][0]
            else:
                return None

    # IMPLEMENT
    def flags(self, index):
        if index.column() == 0:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable
        else:
            return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    # IMPLEMENT
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid():
            if index.column() == 0:
                if value not in self._mocap_list:
                    self._mocap_list[index.row()] = value

        return True

    # IMPLEMENT
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._headers[section]
            else:
                return section  # In this house we start counting from ZERO!

        return None

    def remove(self, index):
        if not index < 0:
            self.beginRemoveRows(QtCore.QModelIndex(), index, index)
            del self._mocap_list[index]
            del self._vertex_list[index]
            try:
                cmds.delete(self._sphere_list[index])
            except RuntimeError:
                pass
            del self._sphere_list[index]
            self.endRemoveRows()

    def add(self, mocap, wildcard=None):
        if mocap not in self._mocap_list or mocap == wildcard:
            vertex_data = self._get_vertex_data()
            if vertex_data is None:
                return False

            if vertex_data not in self._vertex_list:
                self.add_row(mocap, vertex_data)
                mel.eval('doMenuComponentSelection("{}", "vertex")'.format(
                    vertex_data[0]))
                return True

        mel.eval('doMenuComponentSelection("{}", "vertex")'.format(
            vertex_data[0]))
        return False

    def set_vertex(self, index):
        if index < 0:
            return

        vertex_data = self._get_vertex_data()
        if vertex_data is None:
            return False

        self._vertex_list[index] = vertex_data
        try:
            if self._sphere_list[index] is not None:
                cmds.delete(self._sphere_list[index])
        except RuntimeError:
            pass
        self._sphere_list[index] = self._create_sphere(vertex_data)
        self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole])
        mel.eval('doMenuComponentSelection("{}", "vertex")'.format(
            vertex_data[0]))

    def _get_vertex_data(self):
        vertex_data = cmds.ls(selection=True, showType=True)
        if len(vertex_data) != 2:
            return None
        if vertex_data[1] != "float3":
            return None

        vtx_data = vertex_data[0].rsplit(".", 2)  # Object
        if not vtx_data[1].startswith("vtx"):
            return None

        vtx_data[1] = vtx_data[1][3:]
        vtx_data[1] = vtx_data[1][1:-1]  # Index number
        return vtx_data

    def add_row(self, mocap, vertex_data, make_sphere=True):
        self.beginInsertRows(QtCore.QModelIndex(), len(
            self._mocap_list), len(self._mocap_list))
        self._mocap_list.append(mocap)
        self._vertex_list.append(vertex_data)
        if make_sphere:
            self._sphere_list.append(self._create_sphere(vertex_data))
        else:
            self._sphere_list.append(None)
        self.endInsertRows()

    def _create_sphere(self, vertex_data):
        sphere = cmds.polySphere(radius=self._SPHERE_DEF_SIZE)
        cmds.select(sphere)
        cmds.hyperShade(assign=self._shader_node)
        cmds.select(vertex_data[0] + ".vtx[" + vertex_data[1] + "]")
        cmds.select(sphere, add=True)
        mel.eval(
            'doCreatePointOnPolyConstraintArgList 1 { "0","0","0","1","","1" };')
        return sphere

    def _setup_sphere_shader(self):
        self._shader_node = cmds.shadingNode(
            "phong", asShader=True, name="VertexSphereColor")
        cmds.setAttr(self._shader_node + ".color", 1, 1, 0, type="double3")
        self._selected_shader_node = cmds.shadingNode(
            "phong", asShader=True, name="VertexSphereColorSelected")
        cmds.setAttr(self._selected_shader_node +
                     ".color", 1, 0, 0, type="double3")

    def set_mocap(self, index, mocap, wildcard=None):
        if mocap not in self._mocap_list or mocap == wildcard:
            self._mocap_list[index] = [mocap]
            self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole])

    def populate_mocap(self, mocap_list):
        for mocap in mocap_list:
            self.add_row(mocap, ["N", "A"], make_sphere=False)

    def get_mocap_list(self):
        return self._mocap_list

    def get_vertex_list(self):
        return self._vertex_list

    def highlight(self, index):
        if not index < 0:
            for sphere in self._sphere_list:
                if sphere is not None:
                    cmds.select(sphere)
                    cmds.hyperShade(assign=self._shader_node)

            if self._sphere_list[index] is not None:
                cmds.select(self._sphere_list[index])
                cmds.hyperShade(assign=self._selected_shader_node)
                cmds.select(clear=True)

            try:
                mel.eval('doMenuComponentSelection("{}", "vertex")'.format(
                    self._vertex_list[index][0]))
            except ValueError:
                pass

    def load_json(self, data):
        for key in data.keys():
            self.add(key, data[key][self._MODEL_KEY],
                     data[key][self._VERTEX_KEY])

    def get_json(self):
        data = {}
        for i in range(len(self._mocap_list)):
            temp_dict = {
                self._MODEL_KEY: self._vertex_list[i][0], self._VERTEX_KEY: self._vertex_list[i][1]}
            data[self._mocap_list[i]] = temp_dict

        return data

    def can_export_json(self):
        mocap_set = set(self._mocap_list)
        if len(mocap_set) != len(self._mocap_list):
            return False
        return True
