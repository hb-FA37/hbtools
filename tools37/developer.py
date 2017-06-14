import os
import sys
import inspect


_RELOAD_EXCEPTION_MODULES = ["os", "sys", "inspect"]


def reload(user_path=None):
    """ Resets the session by deleting all the loaded modules from the given user_path.
    If no path is provided the entire workspace will be reloaded.

    Credits for this one go to: Nick Rodgers
    https://medium.com/@nicholasRodgers/sidestepping-pythons-reload-function-without-restarting-maya-2448bab9476e
    """
    if user_path is None:
        user_path = os.path.dirname(__file__)
        user_path = os.path.abspath(os.path.join(user_path, ("..")))

    user_path = user_path.lower()
    print "Reloading everything below: {}".format(user_path)

    modules_to_delete = {}
    for key in sys.modules.keys():
        if key in _RELOAD_EXCEPTION_MODULES:
            # Certain modules should never be unloaded, for example those used
            # in here.
            continue

        if sys.modules[key] is None:
            # None case.
            continue

        try:
            module_file_path = inspect.getfile(sys.modules[key])
            module_file_path = module_file_path.lower()
        except TypeError:
            continue

        base_init = os.path.join(os.path.dirname(__file__.lower()), "__init__.pyc")
        if module_file_path == __file__.lower() or module_file_path == base_init:
            # Don't remove the sripts hierarchy, this will break everything.
            continue

        if module_file_path.startswith(user_path):
            modules_to_delete[key] = module_file_path

    for key in sorted(modules_to_delete.keys()):
        module_path = modules_to_delete[key]
        print "Deleting module {} located at {}".format(key, module_path)
        del sys.modules[key]
