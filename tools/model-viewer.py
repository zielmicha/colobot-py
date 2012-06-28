import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import g3d
import g3d.camera_drivers
import modfile

loader = modfile.Loader()
loader.add_modfile('colobot.data/colobot1.dat')
loader.add_modfile('colobot.data/colobot2.dat')
loader.add_directory('colobot.data/diagram')

model = loader.get_model(sys.argv[1])

g3d.options.enable_textures = True

win = g3d.Window()
win.root.add(model)

g3d.camera_drivers.LookAtCameraDriver().install(win)

win.loop()

