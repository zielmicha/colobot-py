#!/usr/bin/python
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import g3d
import g3d.gl
import g3d.camera_drivers
import modfile

loader = modfile.Loader()
loader.add_directory('data/models')
loader.add_directory('data/diagram')
loader.add_directory('data/textures')

model = loader.get_model(sys.argv[1])

g3d.options.enable_textures = True

win = g3d.gl.Window()
win.root.add(model)

g3d.camera_drivers.LookAtCameraDriver().install(win)

win.loop()

