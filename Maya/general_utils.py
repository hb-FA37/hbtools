
def install_packages(packages):
    # try:
    #     from setuptools.command import easy_install
    # except ImportError, e:
    #     print("Import Error:")
    #     print(e)
    #     print("Installing setuptools...")
    #     import ez_setup
    #     result = ez_setup.main()
    #     if result == 0:
    #         print("setuptools installed, retrying import...")
    #         from setuptools.command import easy_install
    #         print("setuptools imported succesfully.")
    #     else:
    #         print("easy_setup installation failed, cannot install packages.")
    #         return
    # Above doesn't work, opens a new Maya instance for some reason.
    # Call the mayapy.exe with the ez_setup.py file as argument instead.
    from setuptools.command import easy_install
    if isinstance(packages, list):
        easy_install.main(packages)
    else:
        easy_install.main([packages])


def load_default_shelves2016():
    shelves = ["shelf_Animation", "shelf_CurvesSurfaces", "shelf_FX",
           "shelf_FXCaching", "shelf_Polygons", "shelf_Rendering",
           "shelf_Rigging", "shelf_Sculpting", "shelf_XGen"]
    _load_shelves(shelves)


def load_default_shelves2017():
    shelves = ["shelf_Animation", "shelf_Arnold", "shelf_Bifrost",
               "shelf_CurvesSurfaces", "shelf_FX", "shelf_FXCaching", 
               "shelf_MASH", "shelf_MotionGraphics", "shelf_Polygons", 
               "shelf_Rendering", "shelf_Rigging", "shelf_Sculpting", 
               "shelf_TURTLE", "shelf_XGen"]
    _load_shelves(shelves)


def _load_shelves(shelves):   
    for shelf in shelves:
        try:
            mel.eval('loadNewShelf "{}.mel";'.format(shelf))
        except RuntimeError, e:
            print "Cannot load {}".format(shelf)
            print e
    
    mel.eval('saveAllShelves $gShelfTopLevel;')
