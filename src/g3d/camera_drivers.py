# Copyright (c) 2012, Michal Zielinski <michal@zielinscy.org.pl>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#     * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 
#     * Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

' Camera drivers for interactive model viewing. '
import g3d
import g3d.gl
import math

from g3d import Vector2, Vector3, Quaternion
from g3d.gl import Keys

class CameraDriver(g3d.gl.EventHandler):
    def __init__(self):
        self.camera = g3d.gl.Camera()
    
    def install(self, window):
        window.camera = self.camera
        window.event_handler = self

class LookAtCameraDriver(CameraDriver):
    ''' Camera is on sphere with object in its center, always pointed on it. '''
    def __init__(self, radius=35, look_at=Vector3(0, 0, 0)):
        CameraDriver.__init__(self)
        self.radius = radius
        self.last_pos = None

        assert look_at == Vector3(0, 0, 0), 'look_at != (0, 0, 0) not yet supported'
        
        self.camera.center = look_at
        self.camera.eye = Vector2()
        self.spherical = Vector2(math.pi/4, math.pi/4)

        self._update()
    
    def motion(self, pos):
        if self.last_pos is not None:
            delta = pos - self.last_pos
            delta /= 30.
            self.spherical += delta
            self._update()

            self.last_pos = pos

    def _update(self):
        # TODO: handle cases when look_at != (0, 0)
        self.camera.eye = Vector3(
            self.radius * math.sin(self.spherical.x) * math.cos(self.spherical.y),
            self.radius * math.sin(self.spherical.x) * math.sin(self.spherical.y),
            self.radius * math.cos(self.spherical.x),
        )
        self.camera.up = Vector3(0, 1, 0)
        #(Quaternion.new_rotate_axis(-math.pi/2, Vector3(1, 1, 0)) * self.camera.eye).normalized()
            
    def mouse_down(self, button, pos):
        self.last_pos = pos

    def mouse_up(self, button, pos):
        self.last_pos = None

    def mouse_wheel(self, dir):
        const = 1.1
        if dir == -1:
            self.radius *= const
        else:
            self.radius /= const

        self._update()


class FreeCameraDriver(CameraDriver):
    def __init__(self):
        CameraDriver.__init__(self)
        self.camera.eye = Vector3(0, 0, 0)
        self.camera.up = Vector3(0, 0, 1)
        self.speed = Vector3(0, 0, 0)
        self.angular_speed = 0
        self.angle = 0
        
        self._update()

    def _update(self):
        direction = Quaternion.new_rotate_axis(self.angle, Vector3(0, 0, 1)) * Vector3(1, 0, 0)
        self.camera.center = self.camera.eye + direction

    def install(self, window):
        CameraDriver.install(self, window)
        window.timer.add_ticker(self.tick)

    def tick(self, elapsed):
        self.angle += self.angular_speed * elapsed
        self.camera.eye += Quaternion.new_rotate_axis(self.angle, Vector3(0, 0, 1)) * self.speed * elapsed
        
        self._update()
        
    def key_down(self, key):
        if key in (Keys.K_LEFT, Keys.K_RIGHT):
            self.angular_speed = (1 if key == Keys.K_LEFT else -1) * 0.1
        dirs = {
            Keys.K_UP: Vector3(1, 0, 0),
            Keys.K_DOWN: Vector3(-1, 0, 0),
            Keys.K_RSHIFT: Vector3(0, 0, 1),
            Keys.K_RCTRL: Vector3(0, 0, -1),
            Keys.K_LSHIFT: Vector3(0, 0, 1),
            Keys.K_LCTRL: Vector3(0, 0, -1),
        }
        direction = dirs.get(key)
        if direction:
            self.speed = direction
        
    def key_up(self, key):
        self.speed = Vector3()
        self.angular_speed = 0
