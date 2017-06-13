import os
import imp
from distutils.core import setup
from setuptools import find_packages


def get_deps(*args):
    deps = []
    for mod in args:
        try:
            imp.find_module(mod)
        except ImportError:
            deps.append(mod)
    return deps


setup(
    name="tools37",
    version="0.1.0",
    description="Tools37",
    url="https://github.com/hb-FA37/Tools37",
    packages=find_packages(os.path.dirname(__file__)),
    install_requires=get_deps("numpy", "scipy", "moviepy", "Qt.py")
)
