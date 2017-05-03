
def install_package(packages):
    try:
        from setuptools.command import easy_install
    except ImportError, e:
        print("Import Error:")
        print(e)
        print("Installing setuptools...")
        import ez_setup
        result = ez_setup.main()
        if result == 0:
            print("setuptools installed, retrying import...")
            from setuptools.command import easy_install
            print("setuptools imported succesfully.")
        else:
            print("easy_setup installation failed, cannot install packages.")
            return

    if isinstance(packages, list):
        easy_install.main(packages)
    else:
        easy_install([packages])
