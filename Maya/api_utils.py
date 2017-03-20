import maya.OpenMaya as OpenMaya

def get_available_function_sets(mobject):
    # Get all attributes and filter to the function sets.
    dummy_object = OpenMaya.MFn()
    class_variables = [attr for attr in dir(dummy_object) if not callable(getattr(dummy_object, attr)) and not attr.startswith ("__") and not attr.startswith("_")]
    class_variables.remove("nodeType")
    class_variables.remove("this")  
    function_set_dict = {name: getattr(dummy_object, name) for name in class_variables}
   
    # Get functions set for object.
    result_list =  []
    for key in function_set_dict.keys():
        if mobject.hasFn(function_set_dict[key]):
            result_list.append(key)
   
    return result_list
