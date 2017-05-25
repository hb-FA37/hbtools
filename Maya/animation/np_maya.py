import numpy as np
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim


### Maya to Numpy Data ###


def get_blendshape_mat(bs_node_name, indices=None, include_z=True, apply_vertex_weight_map=True):
    """ A mat of a blendshape node, only collects the vertices that are in indices or all """
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
            rows = 3*vertex_count
        else:
            rows = 2*vertex_count
    else: 
        if include_z:
            rows = 3*len(indices)
        else:
            rows = 2*len(indices)

    matrix = np.zeros( (rows, input_target_group_plug.numElements()) )
    target_group_indices = OpenMaya.MIntArray()
    input_target_group_plug.getExistingArrayAttributeIndices(target_group_indices)
    print "Iterating over {} input targets".format(input_target_group_plug.numElements())
    print "Iterating over {}".format(target_group_indices)

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
            
            print "Processing {}, has weight map = {}".format(i, has_vertex_weight_map)
                    
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
                        matrix[3*m_index, column_counter] = target_points[j].x * weight_val
                        matrix[3*m_index+1, column_counter] = target_points[j].y * weight_val
                        matrix[3*m_index+2, column_counter] = target_points[j].z * weight_val
                    else:
                        matrix[2*m_index, column_counter] = target_points[j].x * weight_val
                        matrix[2*m_index+1, column_counter] = target_points[j].y * weight_val

                except ValueError as e:
                    # print "Value error in {}".format(i)
                    # print e
                    # Should only happen when target_indices[j] is not in indices
                    pass

            column_counter = column_counter + 1
        else:
            print "Faulty blendshape in {}, aborting".format(i)
            return None

    return matrix, target_group_indices


def get_vtx_mat(shape_node_name, indices=None, include_z=True, include_index=False) : 
    """ Returns a list of m_index;x;y;z strings """
    
    vtx_index_list = cmds.getAttr(shape_node_name+".vrts", multiIndices=True)

    vtx_world_points = None
    rows = 0
    if indices is not None:
        rows = len(indices)
    else: 
        rows = len(vtx_index_list)

    if include_index:
        if include_z:
            vtx_world_points = np.zeros( (rows, 4) )
        else:
            vtx_world_points = np.zeros( (rows, 3) )
    else:
        if include_z:
            vtx_world_points = np.zeros( (rows, 3) )
        else:
            vtx_world_points = np.zeros( (rows, 2) ) 

    row_counter = 0
    for i in vtx_index_list :
        if indices is None:
            position = cmds.xform(str(shape_node_name)+".pnts["+str(i)+"]", query=True, translation=True, worldSpace=True)
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
                position = cmds.xform(str(shape_node_name)+".pnts["+str(i)+"]", query=True, translation=True, worldSpace=True)
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


def save_blendshape_mat_fabric(bs_node_name, file_path, indices=None, include_z=True, apply_vertex_weight_map=True):
    """ Collets the data of ablendshape node, and saves it to file_path to be processed in fabric """
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
        rows = vertex_count
    else: 
        rows = len(indices)

    target_group_indices = OpenMaya.MIntArray()
    input_target_group_plug.getExistingArrayAttributeIndices(target_group_indices)
    print "Iterating over {} input targets".format(input_target_group_plug.numElements())
    print "Iterating over {}".format(target_group_indices)

    """
    Note: Physical vs Logical index
    Physical index: list access by 0 -> len(list), ignores gaps in the true indexes (the logical ones)
    Logical index: list reduced to only the indexes it has, access by its TRUE index, visible in node editor
    """
    counter = 0
    len_counter = len(str(target_group_indices.length()))
    for i in target_group_indices:
        if include_z:
            matrix = np.zeros( (rows, 4) )
        else:
            matrix = np.zeros( (rows, 3) )

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
            
            print "Processing {}, has weight map = {}".format(i, has_vertex_weight_map)
                    
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
                        matrix[m_index, 0] = target_points[j].x * weight_val
                        matrix[m_index, 1] = target_points[j].y * weight_val
                        matrix[m_index, 2] = target_points[j].z * weight_val
                        matrix[m_index, 3] = target_indices[j]
                    else:
                        matrix[m_index, 0] = target_points[j].x * weight_val
                        matrix[m_index, 1] = target_points[j].y * weight_val
                        matrix[m_index, 2] = target_indices[j]

                except ValueError as e:
                    # print "Value error in {}".format(i)
                    # print e
                    # Should only happen when target_indices[j] is not in indices
                    pass

            save_txt = file_path.format(str(counter).rjust(len_counter, "0"))
            np.savetxt(save_txt, matrix)
            counter = counter + 1
        else:
            print "Faulty blendshape in {}, aborting".format(i)
            return None


### Matrix Analysis ###


def get_zero_columns(matrix):
    """ Returns a list of the columns which are all 0 """
    rows =  matrix.shape[0]
    columns = matrix.shape[1]
    
    result = []
    for j in range(columns):
        is_zero_column = True
        for i in range(rows):
            is_zero_column = is_zero_column and matrix[i,j] == 0.0
        result.append(is_zero_column)
        
    return result


def filter_zero_columns(matrix, debug=False):
    """ Returns the matrix without zero columns and which columns where removed """
    zero_list = get_zero_columns(matrix)
    
    columns = zero_list.count(False)
    rows = matrix.shape[0]
    
    filtered = np.zeros( (rows, columns) )
    removed = []
    counter = 0
    
    for i in range(len(zero_list)):
        if not zero_list[i]:
            filtered[:, counter] = matrix[:, i]
            counter = counter + 1
        else:
            removed.append(i)
            if debug:
                print "Removed column index " + str(i)
            
    return filtered, removed


### Procrustus ###


def procrustes(X, Y, scaling=True, reflection='best'):
    """
    A port of MATLAB's `procrustes` function to Numpy.

    Procrustes analysis determines a linear transformation (translation,
    reflection, orthogonal rotation and scaling) of the points in Y to best
    conform them to the points in matrix X, using the sum of squared errors
    as the goodness of fit criterion.

        d, Z, [tform] = procrustes(X, Y)

    Inputs:
    ------------
    X, Y    
        matrices of target and input coordinates. they must have equal
        numbers of  points (rows), but Y may have fewer dimensions
        (columns) than X.

    scaling 
        if False, the scaling component of the transformation is forced
        to 1

    reflection
        if 'best' (default), the transformation solution may or may not
        include a reflection component, depending on which fits the data
        best. setting reflection to True or False forces a solution with
        reflection or no reflection respectively.

    Outputs
    ------------
    d       
        the residual sum of squared errors, normalized according to a
        measure of the scale of X, ((X - X.mean(0))**2).sum()

    Z
        the matrix of transformed Y-values

    tform    
        a dict specifying the rotation, translation and scaling that
        maps X --> Y

    """

    n,m = X.shape
    ny,my = Y.shape

    muX = X.mean(0)
    muY = Y.mean(0)

    X0 = X - muX
    Y0 = Y - muY

    ssX = (X0**2.).sum()
    ssY = (Y0**2.).sum()

    # Centred Frobenius norm
    normX = np.sqrt(ssX)
    normY = np.sqrt(ssY)

    # Scale to equal (unit) norm
    X0 /= normX
    Y0 /= normY

    if my < m:
        Y0 = np.concatenate((Y0, np.zeros(n, m-my)),0)

    # Optimum rotation matrix of Y
    A = np.dot(X0.T, Y0)
    U,s,Vt = np.linalg.svd(A,full_matrices=False)
    V = Vt.T
    T = np.dot(V, U.T)

    if reflection is not 'best':

        # Does the current solution use a reflection?
        have_reflection = np.linalg.det(T) < 0

        # Ff that's not what was specified, force another reflection
        if reflection != have_reflection:
            V[:,-1] *= -1
            s[-1] *= -1
            T = np.dot(V, U.T)

    traceTA = s.sum()

    if scaling:

        # Optimum scaling of Y
        b = traceTA * normX / normY

        # Standarised distance between X and b*Y*T + c
        d = 1 - traceTA**2

        # Transformed coordinates
        Z = normX*traceTA*np.dot(Y0, T) + muX

    else:
        b = 1
        d = 1 + ssY/ssX - 2 * traceTA * normY / normX
        Z = normY*np.dot(Y0, T) + muX

    # Transformation matrix
    if my < m:
        T = T[:my,:]
    c = muX - b*np.dot(muY, T)

    # Transformation values 
    tform = {'rotation':T, 'scale':b, 'translation':c}

    return d, Z, tform


def apply_procrustus_transform(Y, tform):
    Z = tform['scale']*np.dot(Y, tform['rotation']) + tform['translation']
    return Z