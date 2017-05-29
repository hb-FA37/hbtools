import maya.cmds as cmds
import maya.OpenMaya as OpenMaya


def get_vtx_position(shape_node):
    vtx_world_positions = []  # [ [index, x, y, z], ... ]
    vtx_index_list = cmds.getAttr(shape_node + ".vrts", multiIndices=True)

    for i in vtx_index_list:
        point_position = cmds.xform(str(shape_node) + ".pnts[" + str(i) + "]", query=True, translation=True, worldSpace=True)
        vtx_world_positions.append(point_position)

    return vtx_world_positions


def set_blendshape_weights(blendshape_node, weights, clamp=True):
    weight_attrs = cmds.listAttr(blendshape_node + ".weight", multi=True)
    if len(weight_attrs) != len(weights):
        print "Error: number weights != num of attributes"
        return

    for i, attr in enumerate(weights):
        if clamp:
            if weights[i] > 1:
                cmds.setAttr(blendshape_node + "." + attr, 1)
            elif weights[i] < 0:
                cmds.setAttr(blendshape_node + "." + attr, 0)
            else:
                cmds.setAttr(blendshape_node + "." + attr, weights[i])
        else:
            cmds.setAttr(blendshape_node + "." + attr, weights[i])


def set_blendshape_weights_to(blendshape_node, weight):
    weight_attrs = cmds.listAttr(blendshape_node + ".weight", multi=True)
    for attr in weight_attrs:
        cmds.setAttr(blendshape_node + "." + attr, weight)
