import os
import sys
import json
import maya.cmds as cmds

import scipy.optimize as sp
import hbtools.maya.mesh_utils as mu
import hbtools.maya.maya2numpy as m2n


class BlendshapeCalculator(object):
    def __init__(self, blendshape, output_mesh, z=True, debug=False):
        self._debug = debug             # Print debug statements.
        self._z = z                     # Use z-axis for calculation.
        # Scene data
        self._output_mesh = output_mesh
        self._blendshape_node = blendshape
        # Indices
        self._indices = []
        # Raw data
        self._blendshape_mat = None      # Raw Blendshape Matrix
        self._blendshape_indices = None  # Target Indices List
        self._neutral_mesh = None

        # Calculation data
        self._removed_cols = None

        self.reload()

    # Data loading #

    def reload(self):
        """ Reloads the raw geometry data from Maya. """
        self.load_neutral_mesh()
        self.load_blendshape()

    def load_blendshape(self):
        """ Inits the blendshape matrix. """
        blendshape, indices = m2n.get_blendshape_mat(self._blendshape_node, indices=self._indices, include_z=self._z)
        self._blendshape_mat = blendshape
        self._blendshape_indices = indices
        self._filter_blendshape()

    def load_neutral_mesh(self):
        """ Inits the neutral matrix. """
        mu.set_blendshape_weights_to(self._blendshape_node, 0.0)
        self._neutral_mesh = m2n.get_vtx_mat(self._output_mesh, indices=self._indices, include_z=self._z)
        self._neutral_mesh = self._neutral_mesh.flatten()
        if self._debug:
            message = "Neutral Shape: {}".format(self._neutral_mesh.shape)
            sys.stdout.write(message)
        # TODO; add filtering method to circumvent changing weights reloading the entire mesh.

    def _filter_blendshape(self):
        a, b = m2n.filter_zero_columns(self._blendshape_mat, debug=True)
        self._filtered_blendshape = a
        self._removed_cols = b

        if self._debug:
            sys.stdout.write("Removed Columns: {} \n".format(self._removed_cols))
            sys.stdout.write("Blendshape Shape: ".ljust(20, " ") + str(self._blendshape_mat.shape) + "\n")
            sys.stdout.write("Filtered Shape: ".ljust(20, " ") + str(self._filtered_blendshape.shape) + "\n")

    # Vertex Indices #

    def set_vertex_indices(self, indices):
        """ Loads the indices to be used. """
        self._indices = indices

    def add_index(self, index, reload_=True):
        self._indices.append(index)
        self._indices = sorted(self._indices)
        if reload_:
            self.reload()

    def remove_index(self, index):
        try:
            self._indices.remove(index)
        except ValueError, e:
            pass

    def clear_vertex_indices(self):
        self._indices = []

    # Calculations #

    def calculate_weights(self, target_points, update=True):
        # diff = target_points - self._neutral_mesh
        diff = target_points  # TODO; check if true.

        weights, error = sp.nnls(self._filtered_blendshape, diff)
        weights = [wi for wi in weights]

        # Insert zero columns back in
        for i in range(len(self._removed_cols)):
            weights.insert(self._removed_cols[i] + i, 0)

        if self._debug:
            sys.stdout.write("Weights: {} \n".format(weights))
            sys.stdout.write("Error: {} \n".format(error))

        if update:
            mu.set_blendshape_weights(self._blendshape_node, weights)

        return weights


# Maya Scene Debug Helpers #


def draw_debug_spheres(X, Y, Z, use_z=True):
    nodes_X = draw_debug_spheres_single(X, (1, 0, 0, "VertexSphereColorX"), "GroupModel", use_z)
    nodes_Y = draw_debug_spheres_single(X, (0, 1, 0, "VertexSphereColorY"), "GroupMocap", use_z)
    nodes_Z = draw_debug_spheres_single(X, (0, 0, 1, "VertexSphereColorZ"), "GroupApprox", use_z)

    triangle_group = cmds.group(name="GroupTris", empty=True)
    triangle_shader_node = cmds.shadingNode("phong", asShader=True, name="VertexSphereColorTris")
    cmds.setAttr(triangle_shader_node + ".color", 1, 0, 1, type="double3")

    nodes = [triangle_shader_node, triangle_group]
    for i in range(2, len(nodes_X)):
        point1 = cmds.getAttr(nodes_X[i] + ".translate")
        point2 = cmds.getAttr(nodes_Y[i] + ".translate")
        point3 = cmds.getAttr(nodes_Z[i] + ".translate")
        triangle = cmds.polyCreateFacet(p=[point1, point2, point3])
        cmds.parent(triangle, triangle_group)
        cmds.select(triangle)
        cmds.hyperShade(assign=triangle_shader_node)
        nodes.append(triangle)

    nodes.extend(nodes_X)
    nodes.extend(nodes_Y)
    nodes.extend(nodes_Z)

    return nodes


def draw_debug_spheres_single(points, shader=(1, 0, 0, "sphere_STND"), group=None, use_z=True):
    shader_node = cmds.shadingNode("phong", asShader=True, name=shader[3])
    cmds.setAttr(shader_node + ".color", shader[0], shader[1], shader[2], type="double3")
    group_node = cmds.group(name=group, empty=True)

    nodes = [shader_node, group_node]
    for i in range(points.shape[0]):
        if use_z:
            xz = points[i, 2]
        else:
            xz = 10
        nodes.append(create_debug_sphere(points[i, 0], points[i, 1], xz, shader_node, group_node))

    return nodes


def create_debug_sphere(x, y, z, shader=None, group=None, radius=0.1):
    sphere = cmds.polySphere(radius=radius)[0]
    cmds.setAttr(sphere + ".translateX", x)
    cmds.setAttr(sphere + ".translateY", y)
    cmds.setAttr(sphere + ".translateZ", z)
    cmds.select(sphere)

    if shader is not None:
        cmds.hyperShade(assign=shader)

    if group is not None:
        cmds.parent(sphere, group)

    return sphere
