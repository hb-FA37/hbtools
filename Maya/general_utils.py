
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
    # Above doesn't work, opens a new maya instance for some reason
    # call the mayapy.exe with the ez_setup.py file as argument instead

    from setuptools.command import easy_install
    if isinstance(packages, list):
        easy_install.main(packages)
    else:
        easy_install.main([packages])
