import maya.cmds as cmds
import maya.OpenMaya as OpenMaya


def get_vtx_position(shape_node):
    vtx_world_positions = []  # [ [index, x, y, z], ... ]
    vtx_index_list = cmds.getAttr(shape_node + ".vrts", multiIndices=True)

    for i in vtx_index_list:
        point_position = cmds.xform(str(shape_node) + ".pnts[" + str(i) + "]", query=True, translation=True, worldSpace=True)
        vtx_world_positions.append(point_position)

    return vtx_world_positions
