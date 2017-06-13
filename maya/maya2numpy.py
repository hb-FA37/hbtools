import numpy as np
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim

"""
Collection of methods to gather Maya data into Numpy structures.
"""


def get_blendshape_mat(bs_node_name, indices=None, include_z=True, apply_vertex_weight_map=True):
    """ A mat of a blendshape node, only collects the vertices that are in indices or all
    Returns a mat of the form:
    X X X...
    Y Y Y
    Z Z Z
    X X X
    Y Y Y
    ...
    """
    bs_node_obj = OpenMaya.MObject()
    sel = OpenMaya.MSelectionList()
    sel.add(bs_node_name, 0)
    sel.getDependNode(0, bs_node_obj)

    bs_node = OpenMaya.MFnDependencyNode(bs_node_obj)
    input_target_group_plug = bs_node.findPlug('inputTarget').elementByPhysicalIndex(0).child(0)

    output_mesh = bs_node.findPlug('outputGeometry').elementByPhysicalIndex(0).asMObject()
    output_mesh = OpenMaya.MFnMesh(output_mesh)
    vertex_count = output_mesh.numVertices()

    rows = -1
    if indices is None:
        if include_z:
            rows = 3 * vertex_count
        else:
            rows = 2 * vertex_count
    else:
        if include_z:
            rows = 3 * len(indices)
        else:
            rows = 2 * len(indices)

    matrix = np.zeros((rows, input_target_group_plug.numElements()))
    target_group_indices = OpenMaya.MIntArray()
    input_target_group_plug.getExistingArrayAttributeIndices(target_group_indices)
    # print "Iterating over {} input targets".format(input_target_group_plug.numElements())
    # print "Iterating over {}".format(target_group_indices)

    """
    Note: Physical vs Logical index
    Physical index: list access by 0 -> len(list), ignores gaps in the true indexes (the logical ones)
    Logical index: list reduced to only the indexes it has, access by its TRUE index, visible in node editor
    """

    column_counter = 0
    for i in target_group_indices:
        input_target_6000_plug = input_target_group_plug.elementByLogicalIndex(i).child(0).elementByPhysicalIndex(0)

        # Vertices / Points
        input_points_target = input_target_6000_plug.child(3).asMObject()
        fn_points = OpenMaya.MFnPointArrayData(input_points_target)
        target_points = OpenMaya.MPointArray()
        fn_points.copyTo(target_points)

        # Indices
        input_components_target = input_target_6000_plug.child(4).asMObject()
        component_list = OpenMaya.MFnComponentListData(input_components_target)[0]
        fn_index = OpenMaya.MFnSingleIndexedComponent(component_list)
        target_indices = OpenMaya.MIntArray()
        fn_index.getElements(target_indices)

        if target_indices.length() == target_points.length():
            # Weight map.
            has_vertex_weight_map = False
            if apply_vertex_weight_map:
                target_vertex_weight_plug = input_target_group_plug.elementByLogicalIndex(i).child(1)
                if target_vertex_weight_plug.numElements() > 0:
                    weight_indices = OpenMaya.MIntArray()
                    target_vertex_weight_plug.getExistingArrayAttributeIndices(weight_indices)
                    index_counter = 0
                    has_vertex_weight_map = True

            # print "Processing {}, has weight map = {}".format(i, has_vertex_weight_map)

            for j in range(target_indices.length()):
                try:
                    # Index in matrix.
                    m_index = -1
                    if indices is None:
                        m_index = target_indices[j]
                    else:
                        # Follow ordering of indices.
                        m_index = indices.index(target_indices[j])

                    # Weight map value.
                    weight_val = 1.0
                    if has_vertex_weight_map:
                        # Abusing fact that target_indices and weight_indices should be ordered.
                        for k in range(index_counter, target_vertex_weight_plug.numElements()):
                            if weight_indices[k] == target_indices[j]:
                                weight_val = input_target_group_plug.elementByLogicalIndex(i).child(1).elementByLogicalIndex(target_indices[j]).asFloat()
                                # weight_val = cmds.getAttr(bs_node_name+".inputTarget[0].inputTargetGroup[{}].targetWeights[{}]".format(i, target_indices[j]))
                                index_counter = k + 1
                            elif weight_indices[k] < target_indices[j]:
                                pass
                            else:
                                break
                        else:
                            # We either hit a value or iterate over the entire weight_indices once.
                            index_counter = target_vertex_weight_plug.numElements() + 1

                    # Set values.
                    if include_z:
                        matrix[3 * m_index, column_counter] = target_points[j].x * weight_val
                        matrix[3 * m_index + 1, column_counter] = target_points[j].y * weight_val
                        matrix[3 * m_index + 2, column_counter] = target_points[j].z * weight_val
                    else:
                        matrix[2 * m_index, column_counter] = target_points[j].x * weight_val
                        matrix[2 * m_index + 1, column_counter] = target_points[j].y * weight_val

                except ValueError, e:
                    # print "Value error in {}".format(i)
                    # print e
                    # Should only happen when target_indices[j] is not in indices
                    pass

            column_counter = column_counter + 1
        else:
            print "Faulty blendshape in {}, aborting".format(i)
            return None

    return matrix, target_group_indices


def get_vtx_mat(shape_node_name, indices=None, include_z=True, include_index=False):
    """ Returns a list of m_index;x;y;z strings """

    vtx_index_list = cmds.getAttr(shape_node_name + ".vrts", multiIndices=True)

    vtx_world_points = None
    rows = 0
    if indices is not None:
        rows = len(indices)
    else:
        rows = len(vtx_index_list)

    if include_index:
        if include_z:
            vtx_world_points = np.zeros((rows, 4))
        else:
            vtx_world_points = np.zeros((rows, 3))
    else:
        if include_z:
            vtx_world_points = np.zeros((rows, 3))
        else:
            vtx_world_points = np.zeros((rows, 2))

    row_counter = 0
    for i in vtx_index_list:
        if indices is None:
            position = cmds.xform(str(shape_node_name) + ".pnts[" + str(i) + "]", query=True, translation=True, worldSpace=True)
            vtx_world_points[row_counter, 0] = position[0]
            vtx_world_points[row_counter, 1] = position[1]
            if include_z:
                vtx_world_points[row_counter, 2] = position[2]
                if include_index:
                    vtx_world_points[row_counter, 3] = i
            else:
                if include_index:
                    vtx_world_points[row_counter, 2] = i
            row_counter = row_counter + 1
        else:
            if i in indices:
                position = cmds.xform(str(shape_node_name) + ".pnts[" + str(i) + "]", query=True, translation=True, worldSpace=True)
                vtx_world_points[row_counter, 0] = position[0]
                vtx_world_points[row_counter, 1] = position[1]
                if include_z:
                    vtx_world_points[row_counter, 2] = position[2]
                    if include_index:
                        vtx_world_points[row_counter, 3] = i
                else:
                    if include_index:
                        vtx_world_points[row_counter, 2] = i
                row_counter = row_counter + 1

    return vtx_world_points


# Matrix Analysis #


def get_zero_columns(matrix):
    """ Returns a list of the columns which are all 0 """
    rows = matrix.shape[0]
    columns = matrix.shape[1]

    result = []
    for j in range(columns):
        is_zero_column = True
        for i in range(rows):
            is_zero_column = is_zero_column and matrix[i, j] == 0.0
        result.append(is_zero_column)

    return result
