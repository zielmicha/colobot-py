#!/usr/bin/python
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import g3d
import g3d.gl
import g3d.camera_drivers
import g3d.model
import colobot.loader

loader = colobot.loader.Loader()
loader.add_directory('data/models')
loader.add_directory('data/anim')
loader.add_directory('data/diagram')
loader.add_directory('data/textures')

name = sys.argv[1]
if name.endswith('.mod'):
    obj = loader.get_model(name)
else:
    model = g3d.model.read(loader=loader, name=name)
    obj = model.root

g3d.options.enable_textures = True

win = g3d.gl.Window()
win.root.add(obj)

def rotate():
    rot = g3d.Quaternion.new_rotate_axis(3.14 / 180 * 5, g3d.Vector3(0, 1, 0))
    win.root.rotation = win.root.rotation * rot

if name == 'wheeled-transporter.model':
    animator = g3d.model.Animator()
    animator.install(win.timer)
    model.play(animator, 'arm_front')
    
win.timer.add_interval(0.1, rotate)

g3d.camera_drivers.LookAtCameraDriver(radius=50).install(win)

win.loop()

