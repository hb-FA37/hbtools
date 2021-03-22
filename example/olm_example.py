import hbtools.developer as dev
dev.reload()

import os
import maya.cmds as cmds
import hbtools.maya.olm as olm

cmds.file(os.path.join(os.path.dirname(__file__), r"_CubeToSphere.mb"), open=True, prompt=False, force=True)
olm.show_mixin_tool()
