import collections
import maya.cmds as cmds
import maya.mel as mel

from Qt import QtCore


class VertexModel(QtCore.QAbstractTableModel):
    _SPHERE_DEF_SIZE = 0.1
    _MODEL_KEY = "vobject"
    _VERTEX_KEY = "vindex"
    _HEADERS = ["Name", "Vertex"]
    _MAYA_GROUP = "OlmGroup"

    _VD_NAME = "vName"
    _VD_INDEX = "vIndex"
    _VD_VERTEX_SPHERE = "vSphere"
    _VD_CONTROL_SPHERE = "cSphere"
    _VD_CONTROL_GROUP = "vGroup"

    def __init__(self, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._blendshape = None             # Blendshape Name
        self._output_geometry = None        # Output Mesh Name

        self._vertex_data = []
        self._maya_group = cmds.group(name=self._MAYA_GROUP, empty=True)

        self._vertex_sphere_size = self._SPHERE_DEF_SIZE
        self._vertex_shader_node = None            # Vertex Sphere Shader Node
        self._selected_vertex_shader_node = None   # Vertex Sphere Selected Shader Node

        self._control_sphere_size = self._SPHERE_DEF_SIZE
        self._control_shader_node = None            # Vertex Sphere Shader Node
        self._selected_control_shader_node = None   # Vertex Sphere Selected Shader Node

        self._setup_sphere_shaders()

    def delete(self):
        # Shaders
        try:
            cmds.delete(self._vertex_shader_node)
        except RuntimeError:
            pass

        try:
            cmds.delete(self._selected_vertex_shader_node)
        except RuntimeError:
            pass

        try:
            cmds.delete(self._control_shader_node)
        except RuntimeError:
            pass

        try:
            cmds.delete(self._selected_control_shader_node)
        except RuntimeError:
            pass

        # Spheres
        for data in self._vertex_data:
            try:
                cmds.delete(data[self._VD_VERTEX_SPHERE])
            except RuntimeError:
                pass

            try:
                cmds.delete(data[self._VD_CONTROL_SPHERE])
            except RuntimeError:
                pass
            try:
                cmds.delete(data[self._VD_CONTROL_GROUP])
            except RuntimeError:
                pass

    def set_scene_objects(self, blendshape, output_geometry):
        self._blendshape = blendshape
        self._output_geometry = output_geometry

    # Overriden Methods #

    # IMPLEMENT
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._vertex_data)

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
                    return self._vertex_data[i][self._VD_NAME]
                return self._vertex_data[i][self._VD_INDEX]
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
                if value not in self.get_vertex_names():
                    self._vertex_data[index.row()][self._VD_NAME] = value

        return True

    # IMPLEMENT
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._HEADERS[section]
            else:
                return section
        return None

    # Model Methods #

    def remove(self, index):
        if not index < 0:
            self.beginRemoveRows(QtCore.QModelIndex(), index, index)

            try:
                cmds.delete(self._vertex_data[index][self._VD_VERTEX_SPHERE])
            except RuntimeError:
                pass
            try:
                cmds.delete(self._vertex_data[index][self._VD_CONTROL_SPHERE])
            except RuntimeError:
                pass
            try:
                cmds.delete(self._vertex_data[index][self._VD_CONTROL_GROUP])
            except RuntimeError:
                pass

            del self._vertex_data[index]

            self.endRemoveRows()

    def add(self, vertex_index, name=None):
        if vertex_index in self.get_vertex_indices():
            print "Vertex {} already in list".format(vertex_index)

        if name not in self.get_vertex_names():
            if name is None:
                name = ""
            self.add_row(vertex_index, name)
            return True

        return False

    def add_row(self, vertex_index, name):
        self.beginInsertRows(QtCore.QModelIndex(), len(self._vertex_data), len(self._vertex_data))
        vertex_sphere = self._create_vertex_sphere(vertex_index)
        control_sphere, control_group = self._create_control_sphere(vertex_index)
        data = {self._VD_NAME: name,
                self._VD_INDEX: vertex_index,
                self._VD_VERTEX_SPHERE: vertex_sphere,
                self._VD_CONTROL_SPHERE: control_sphere,
                self._VD_CONTROL_GROUP: control_group}
        self._vertex_data.append(data)
        self.endInsertRows()

    def get_vertex_names(self):
        return {data[self._VD_NAME] for data in self._vertex_data}

    def get_vertex_indices(self):
        return sorted({data[self._VD_INDEX] for data in self._vertex_data})

    def get_vertex_spheres(self):
        return {data[self._VD_VERTEX_SPHERE] for data in self._vertex_data}

    def get_control_spheres(self):
        return {data[self._VD_CONTROL_SPHERE] for data in self._vertex_data}

    # Spheres #

    def _create_vertex_sphere(self, vertex_index):
        name = "olm_VSphere_{}".format(vertex_index)
        sphere = cmds.polySphere(name=name, radius=1.0)
        cmds.scale(self._vertex_sphere_size, self._vertex_sphere_size,
                   self._vertex_sphere_size, sphere)

        cmds.parent(sphere, self._maya_group)

        cmds.select(sphere)
        cmds.hyperShade(assign=self._vertex_shader_node)

        cmds.select(self._output_geometry + ".vtx[" + vertex_index + "]")
        cmds.select(sphere, add=True)
        mel.eval('doCreatePointOnPolyConstraintArgList 1 { "0","0","0","1","","1" };')

        return sphere[0]

    def _create_control_sphere(self, vertex_index):
        name = "olm_CSphere_{}".format(vertex_index)
        sphere = cmds.polySphere(name=name, radius=1.0)
        cmds.scale(self._control_sphere_size, self._control_sphere_size,
                   self._control_sphere_size, sphere)

        cmds.parent(sphere, self._maya_group)

        cmds.select(sphere)
        cmds.hyperShade(assign=self._control_shader_node)

        cmds.select(sphere)
        name = "olm_CGroup_{}".format(vertex_index)
        group = cmds.group(name=name)

        cmds.select(self._output_geometry + ".vtx[" + vertex_index + "]")
        cmds.select(group, add=True)
        mel.eval('doCreatePointOnPolyConstraintArgList 1 { "0","0","0","1","","1" };')

        return sphere[0], group

    def _setup_sphere_shaders(self):
        self._vertex_shader_node = cmds.shadingNode(
            "phong", asShader=True, name="VertexSphereColor")
        cmds.setAttr(self._vertex_shader_node + ".color",
                     0, 0, 1, type="double3")  # Blue
        self._selected_vertex_shader_node = cmds.shadingNode(
            "phong", asShader=True, name="VertexSphereColorSelected")
        cmds.setAttr(self._selected_vertex_shader_node +
                     ".color", 0, 1, 0, type="double3")  # Green

        self._control_shader_node = cmds.shadingNode(
            "phong", asShader=True, name="ControlSphereColor")
        cmds.setAttr(self._control_shader_node + ".color",
                     1, 0, 0, type="double3")  # Red
        self._selected_control_shader_node = cmds.shadingNode(
            "phong", asShader=True, name="ControlSphereColorSelected")
        cmds.setAttr(self._selected_control_shader_node +
                     ".color", 1, 1, 0, type="double3")  # Yellow

    def highlight(self, index):
        if not index < 0:
            for sphere in self.get_vertex_spheres():
                cmds.select(sphere)
                cmds.hyperShade(assign=self._vertex_shader_node)

            cmds.select(self._vertex_data[index][self._VD_VERTEX_SPHERE])
            cmds.hyperShade(assign=self._selected_vertex_shader_node)
            cmds.select(clear=True)

            for sphere in self.get_control_spheres():
                cmds.select(sphere)
                cmds.hyperShade(assign=self._control_shader_node)

            cmds.select(self._vertex_data[index][self._VD_CONTROL_SPHERE])
            cmds.hyperShade(assign=self._selected_control_shader_node)
            cmds.select(clear=True)

            cmds.select(self._vertex_data[index][self._VD_CONTROL_SPHERE])

    def resize_control_spheres(self, scale):
        self._control_sphere_size = scale
        sphere_list = self.get_control_spheres()
        self._resize_spheres(sphere_list, scale)

    def resize_vertex_spheres(self, scale):
        self._vertex_sphere_size = scale
        sphere_list = self.get_vertex_spheres()
        self._resize_spheres(sphere_list, scale)

    def _resize_spheres(self, spheres, scale):
        for sphere in spheres:
            try:
                cmds.scale(scale, scale, scale, sphere)
            except RuntimeError, error:
                print error

    # Import / Export #

    def load_json(self, data):
        # TODO; error checking, see if blendshape, outputGeometry and vertices exist.
        self._blendshape = data["blendshape"]
        self._output_geometry = data["outputGeometry"]
        for the_tuple in data["vertexList"]:
            self.add(the_tuple[0], name=the_tuple[1])

    def get_json(self):
        data = {"blendshape": self._blendshape,
                "outputGeometry": self._output_geometry,
                "vertexList": []}

        for i in range(len(self._vertex_data)):
            the_tuple = (self._vertex_data[i][self._VD_INDEX],
                         self._vertex_data[i][self._VD_NAME])
            data["vertexList"].append(the_tuple)

        return data
