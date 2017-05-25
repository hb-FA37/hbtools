import os
import json
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim

import numpy as np
import scipy.optimize as sp

import np_maya as npm
reload(npm)
import np_helper as nph
reload(nph)


class BlendshapeEvaluator(object):
    def __init__(self, neutral_mesh, blendshape, output_blendshape=None, z=True, debug=False):
        self._debug = debug
        self._z = z
        # Blendshape scene data
        self._bs_neutral = neutral_mesh        
        self._bs_node = blendshape
        self._bs_output = output_blendshape
        self._zero_frame = 0
        # Indices
        self._indices = None
        self._bs_indices = []
        # Raw data
        self._blendshape = None
        self._mocap = None
        self._neutral = None
        # Calculation data
        self._filtered_blendshape = None
        self._removed_cols = None

    def init_data(self):
        """ Inits the blendshape and neutral """
        self.init_blendshape()
        self.init_neutral()

    def init_blendshape(self):
        """ Inits the blendshape matrix """
        a, b = npm.get_blendshape_mat(self._bs_node, indices=self._indices, include_z=self._z)
        self._blendshape = a
        self._bs_indices = b
        self.filter_blendshape()

    def init_neutral(self):
        """ Inits the neutral matrix """
        self._neutral = npm.get_vtx_mat(self._bs_neutral, indices=self._indices, include_z=self._z, include_index=False)
        self._neutral = self._neutral.flatten()
        if self._debug:
            print "Neutral Shape: {}".format(self._neutral.shape)

    ### Vertex Indices ###

    def load_vertex_indices(self, mvd_file):
        """ Loads the indices of the vertices to be used from a json file """
        data = nph.load_mocap_vertex_data(mvd_file)
        sorted_data = nph.get_sorted_mocap_vertex_data(data)
        self._indices =[d[1] for d in sorted_data]
        if self._debug:
            print "Loaded Mocap: ".ljust(20, " ") + str([d[0] for d in sorted_data])
            print "Loaded Indices: ".ljust(20, " ") + str(self._indices)

    def clear_vertex_indices(self):
        self._indices = None
    
    ### Mocap ###

    def load_mocap(self, mocap_file):
        """ Loads the mocap data """
        self._mocap = np.loadtxt(mocap_file)
        if not self._z:
            self._mocap  = self._mocap [:, 0:2]
        self._mocap = self._mocap .flatten()
        if self._debug:
            print "Mocap Shape: {}".format(self._mocap.shape)

    ### Calculations ###

    def filter_blendshape(self):
        a, b = npm.filter_zero_columns(self._blendshape, debug=True)
        self._filtered_blendshape = a
        self._removed_cols = b

        if self._debug:
            print "Removed Columns: {}".format(self._removed_cols)
            print "Blendshape Shape: ".ljust(20, " ") + str(self._blendshape.shape)
            print "Filtered Shape: ".ljust(20, " ") + str(self._filtered_blendshape.shape)

    def calculate_weights(self, is_diff=False):
        if is_diff:
            diff = self._mocap
        else:
            diff = self._mocap - self._neutral
        
        w, error = sp.nnls(self._filtered_blendshape, diff)
        weights = [wi for wi in w]

        # Insert zero columns back in
        for i in range(len(self._removed_cols)):
            weights.insert(self._removed_cols[i]+i, 0)
        
        if self._bs_output is not None:
            nph.set_blendshape_weights_array(self._bs_output, weights)

        if self._debug:
            print "Weights: {}".format(weights)
            print "Weighting done!"
            
        return weights


class MocapConverter(object):
    def __init__(self, time=0, debug=False):
        self._debug = debug
        self._zero_time = time
        self._mocap_vertex_data = None # [(Mocap, VertexIndex)]
        self._model = None
        self._model_data = None

    def set_zero_time(self, time):
        self._zero_time = time

    def set_model(self, model_name):
        self._model = model_name
        self._model_data = nph.get_vtx_positions(model_name)
        if self._debug:
            print "Model has {} vertices".format(str(len(self._model_data)))

    def load_vertex_indices(self, mvd_file):
        data = nph.load_mocap_vertex_data(mvd_file)
        self._mocap_vertex_data = nph.get_sorted_mocap_vertex_data(data)
        if self._debug:
            max_index = self._mocap_vertex_data[-1][1]
            print "Mocap has {} points, max index is {}".format(str(len(self._mocap_vertex_data)), max_index)

    def convert_mocap_data(self, start, end, save_file, use_z=True, use_diff=False):
        e, Z, tform = self.calculate_transform(use_z)
        np.savetxt(save_file, Z)
        if use_diff:
            self._iterate_frames(tform, start, end, save_file, use_z, Z)
        else:
            self._iterate_frames(tform, start, end, save_file, use_z)
        print "Converting done!"

    def calculate_transform(self, use_z=True, draw_sphere=False):
        rows = len(self._mocap_vertex_data)
        if use_z:
            X = np.zeros((rows, 3)) # Model vertex coordinates.
            Y = np.zeros((rows, 3)) # Mocap locater coordinates.
        else:
            X = np.zeros((rows, 2))
            Y = np.zeros((rows, 2))     

        for i in range(len(self._mocap_vertex_data)):
            key = self._mocap_vertex_data[i][0]
            v_index = self._mocap_vertex_data[i][1]

            mocap = list(cmds.getAttr(key + ".translate", time=self._zero_time))
            Y[i, 0] = mocap[0][0]
            Y[i, 1] = mocap[0][1]
            if use_z:
                Y[i, 2] = mocap[0][2]
            
            vertex =  self._model_data[v_index]
            X[i, 0] = float(vertex[0])
            X[i, 1] = float(vertex[1])
            if use_z:
                X[i, 2] = float(vertex[2])

        e, Z, tform = npm.procrustes(X, Y) # Error, transformed Y, transformations
        if self._debug:
            print "Error: " 
            print str(e)
            print "Transforms: "
            print str(tform)
            print "X: "
            print str(X)
            print "Y: "
            print str(Y)
            print "Z:"
            print str(Z)

            print "X-Z = Per Element Error:"
            difference = X-Z
            difference_abs = abs(difference)
            for i in range(len(self._mocap_vertex_data)):
                key = self._mocap_vertex_data[i][0]
                key_len = len(key)
                spaces = ""
                for j in range(key_len, 15):
                    spaces = spaces + " "

                print key + spaces + str(difference_abs[i, :]) + "  " + str(difference[i, :])

        if draw_sphere:
            nodes = draw_debug_spheres(X, Y, Z, use_z)

        return e, Z, tform

    def _iterate_frames(self, tform, start, end, save_file, use_z=True, Z_neutral=None):
        index_len = len(str(end))
        file_name, file_ext = os.path.splitext(save_file)

        rows = len(self._mocap_vertex_data)
        for t in range(start, end, 1):
            if use_z:
                Y = np.zeros((rows, 3))
            else:
                Y = np.zeros((rows, 2))

            for i in range(rows):
                key = self._mocap_vertex_data[i][0]
                mocap = list(cmds.getAttr(key + ".translate", time=t))

                Y[i, 0] = mocap[0][0]
                Y[i, 1] = mocap[0][1]
                if use_z:
                    Y[i, 2] = mocap[0][2]

            Z = npm.apply_procrustus_transform(Y, tform)
            if Z_neutral is not None:
                    Z = Z - Z_neutral

            file_suffix = str(t-start)
            for j in range(len(file_suffix), index_len):
                file_suffix = "0"+file_suffix
            
            file_path = file_name + file_suffix + file_ext
            np.savetxt(file_path, Z)


def draw_debug_spheres(X, Y ,Z, use_z=True):
    shader_node_x = cmds.shadingNode("phong", asShader=True, name="VertexSphereColorX")
    cmds.setAttr(shader_node_x+".color", 1, 0, 0, type="double3")
    shader_node_y = cmds.shadingNode("phong", asShader=True, name="VertexSphereColorY")
    cmds.setAttr(shader_node_y+".color", 0, 1, 0, type="double3")
    shader_node_z = cmds.shadingNode("phong", asShader=True, name="VertexSphereColorZ")
    cmds.setAttr(shader_node_z+".color", 0, 0, 1, type="double3")
    shader_node_tris = cmds.shadingNode("phong", asShader=True, name="VertexSphereColorTris")
    cmds.setAttr(shader_node_tris+".color", 1, 0, 1, type="double3")

    group_x = cmds.group(n="GroupModel", em=True)
    group_y = cmds.group(n="GroupMocap", em=True)
    group_z = cmds.group(n="GroupApprox", em=True)
    group_tris = cmds.group(n="GroupTris", em=True)

    nodes = [shader_node_x, shader_node_y, shader_node_z, shader_node_tris, group_x, group_y, group_z, group_tris]

    for i in range(X.shape[0]):
        if use_z:
            xz = X[i, 2]
            yz = Y[i, 2]
            zz = Z[i, 2]
        else:
            xz = 10
            yz = 10
            zz = 10

        nodes.append(create_debug_sphere(X[i, 0], X[i, 1], xz, shader_node_x, group_x))
        nodes.append(create_debug_sphere(Y[i, 0], Y[i, 1], yz, shader_node_y, group_y))
        nodes.append(create_debug_sphere(Z[i, 0], Z[i, 1], zz, shader_node_z, group_z))

        tris = cmds.polyCreateFacet( p=[(X[i, 0], X[i, 1], xz), (Y[i, 0], Y[i, 1], yz), (Z[i, 0], Z[i, 1], zz)] )
        cmds.parent(tris, group_tris)
        nodes.append(tris)
        cmds.select(tris)
        cmds.hyperShade(assign=shader_node_tris)  

    return nodes


def draw_debug_spheres_single(X, color=None, parent=None, use_z=True):
    nodes = []
    for i in range(X.shape[0]):
        if use_z:
            xz = X[i, 2]
        else:
            xz = 10
        nodes.append(create_debug_sphere(X[i, 0], X[i, 1], xz, color, parent))


def create_debug_sphere(x, y, z, color=None, parent=None):
    sphere = cmds.polySphere(radius=0.1)[0]    
    cmds.setAttr(sphere+".translateX", x)
    cmds.setAttr(sphere+".translateY", y)
    cmds.setAttr(sphere+".translateZ", z)
    cmds.select(sphere)

    if color is not None:
        cmds.hyperShade(assign=color)     

    if parent is not None:
        cmds.parent(sphere, parent)

    return sphere
