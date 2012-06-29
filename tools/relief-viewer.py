import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import g3d
import g3d.camera_drivers
import g3d.terrain

terrain = g3d.terrain.Terrain()
terrain.load_from_relief(open(sys.argv[1]))

win = g3d.gl.Window()
win.root.add(terrain.model)

g3d.camera_drivers.FreeCameraDriver().install(win)

win.loop()


