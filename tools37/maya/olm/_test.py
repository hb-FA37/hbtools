import Tools37.developer as dev
dev.reload()

import os
import maya.cmds as cmds
import Tools37.maya.olm as olm

cmds.file(os.path.join(os.path.dirname(olm.__file__), r"_CubeToSphere.mb"), open=True, prompt=False, force=True)
olm.show_mixin_tool()
