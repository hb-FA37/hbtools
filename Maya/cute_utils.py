from Qt import QtWidgets, QtCore
from maya import cmds
from maya import OpenMayaUI as omui


def get_maya_main_window():
    """ Returns the QWidget-object of the main maya application. """
    # for obj in QtWidgets.qApp.topLevelWidgets():
    # qApp is a macro which is equivalent too the line below.
    for obj in QtCore.QCoreApplication.instance().topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj
    raise RuntimeError('Could not find MayaWindow instance')


def delete_window(object_name):
    """ Deletes the given UI object if it exists.
    Note: only requires the tail of the uipath.
    """
    # TODO; add exception for Maya main window
    if cmds.window(object_name, exists=True):
        cmds.deleteUI(object_name, wnd=True)


def print_maya_qobject_tree(print_file=None):
    """ Prints the entire qobject tree for the Maya main window.
    This can take a while, these paths are to be used in combination
    with get_qtobject_for_uipath method.
    Note: these paths are slightly different then the ones used by OpenMayaUI.MQtUtil.
    """
    maya = get_maya_main_window()
    if print_file:
        file_ = open(print_file, "w+")

    _print_qobject_tree(maya, "", file_)
    if print_file:
        file_.close()


def _print_qobject_tree(qobject, path, file_=None):
    """ Prints in a depth first like fashion. """
    name = qobject.objectName()
    path = path + "|" + name

    if file_:
        file_.write(path)
    else:
        print path

    for child in qobject.children():
        _print_qobject_tree(child, path, file_=file_)


def get_qtobject_for_uipath(pathstr):
    """ Returns the QtObject for a Maya UI path.
    Ensure that the path starts from the Maya main window and that there are no \
    empty elements in it as this will fail.
    """
    split_pathstr = pathstr.split("|")
    return _find_qobject(get_maya_main_window(), split_pathstr)


def _find_qobject(qobject, tree_elements):
    """ Helper method to get_qtobject_for_uipath.
    Iterates over the qobject and skips those parts
    of the uitree that have elements that aren't part
    of the uipath that we are looking for
    """
    # Verification
    name = qobject.objectName()
    if name == tree_elements[-1]:
        # Found the thing we want
        return qobject

    if name not in tree_elements:
        # Part of the tree we do not wish to explore.
        return None

    # Depth first iteration
    for child in qobject.children():
        qchild = _find_qobject(child, tree_elements)
        if qchild is None:
            continue
        return qchild

    return None

