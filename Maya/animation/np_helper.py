import json
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim


### Data Loading ###
  

def load_mocap_vertex_data(file_name): 
    """ Loads a dict/json: {mocap : {object: string, vertexInd: string (int)}} """
    mocap_vertex_data = None
    with open(file_name, 'r') as the_file:
        mocap_vertex_data = json.load(the_file)
    return mocap_vertex_data


def get_sorted_mocap_vertex_data(mocap_vertex_data):
    """ returns the data sorted by index in a tuple [(string, int)] """
    data = [(key, int(mocap_vertex_data[key]["vertexInd"])) for key in mocap_vertex_data.keys()]
    data = sorted(data, key=lambda tup: tup[1])
    return data


### Maya ###


def set_time(time):
    animation_controller = OpenMayaAnim.MAnimControl()
    t = OpenMaya.MTime()
    t.setValue(time)
    animation_controller.setCurrentTime(t)


def basic_measure():
    selection = cmds.ls(selection=True)
    if len(selection) != 2:
        print "basic_measure: selection) not 2"
        return

    point1 = selection[0]
    point2 = selection[1]

    split1 = point1.split(".")
    split2 = point2.split(".")

    point_pos1 = cmds.xform(split1[0] + ".pnts[" + split1[1][4:-1] + "]", query=True, translation=True, worldSpace=True)
    point_pos2 = cmds.xform(split2[0] + ".pnts[" + split2[1][4:-1] + "]", query=True, translation=True, worldSpace=True)
    diff = [point_pos2[0] - point_pos1[0], point_pos2[1] - point_pos1[1], point_pos2[2] - point_pos1[2]]

    print "basic_measure: selected " + str(selection)
    print "basic_measure: " + str(diff)


def get_vtx_positions(shape_node) : 
    vtx_world_positions = [] # [ [x, y, z], ... ]
    vtx_index_list = cmds.getAttr(shape_node+".vrts", multiIndices=True)
 
    for i in vtx_index_list:
        point_position = cmds.xform(str(shape_node)+".pnts["+str(i)+"]", query=True, translation=True, worldSpace=True)
        vtx_world_positions.append(point_position)
 
    return vtx_world_positions


def set_blendshape_weights_array(bs_node_name, weights):
    """ cmds version """
    weight_attrs = cmds.listAttr(bs_node_name+".weight", multi=True)
    if len(weight_attrs) != len(weights):
        print "Error: nun weights != num of attributes"
        return

    for i in range(len(weights)):
        # print "Setting " + weight_attrs[i].ljust(20, " ") +  str(weights[i])
        if weights[i] > 1:
            cmds.setAttr(bs_node_name+"."+weight_attrs[i], 1)
        else:
            cmds.setAttr(bs_node_name+"."+weight_attrs[i], weights[i])


def set_blendshape_weights_array2(bs_node_name, weights):
    """ MFnBlendShapeDeformer version """
    bs_node_obj = OpenMaya.MObject()
    sel = OpenMaya.MSelectionList()
    sel.add(bs_node_name, 0)
    sel.getDependNode(0, bs_node_obj)

    if bs_node_obj.hasFn(OpenMaya.MFn.kBlendShape):
        blendshape =  OpenMayaAnim.MFnBlendShapeDeformer(bs_node_obj) 
    else:
        print "Error: not a blendshape object."
        return
    
    weight_indices = OpenMaya.MIntArray()
    blendshape.weightIndexList(weight_indices)

    if len(weights) != len(weight_indices):
        print "Error: num of weights != weight_indices"
        return

    for i in range(len(weight_indices)):
        if weights[i] > 1:
            blendshape.setWeight(weight_indices[i], 1)
        else:
            blendshape.setWeight(weight_indices[i], weights[i])


def key_blendshape(bs_node_name):
    bs_node_obj = OpenMaya.MObject()
    sel = OpenMaya.MSelectionList()
    sel.add(bs_node_name, 0)
    sel.getDependNode(0, bs_node_obj)

    if bs_node_obj.hasFn(OpenMaya.MFn.kBlendShape):
        blendshape =  OpenMayaAnim.MFnBlendShapeDeformer(bs_node_obj) 
    else:
        print "Error: not a blendshape object."
        return
    
    weight_indices = OpenMaya.MIntArray()
    blendshape.weightIndexList(weight_indices)

    for i in weight_indices:
        cmds.setKeyframe("{}.w[{}]".format(bs_node_name, i))
