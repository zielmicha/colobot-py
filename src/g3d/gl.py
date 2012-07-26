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
import g3d
import g3d.serialize
from g3d import Vector2, Vector3

from OpenGL import GL, GLU
from OpenGL.GL import *

import numpy
import pygame
import time

MODULE_SERIAL_ID = 3

class Window:
    def __init__(self):
        self.root = g3d.Container()
        self.camera = Camera()
        self.event_handler = EventHandler()
        self.timer = g3d.Timer() # UI timer

    def loop(self):
        self._init()

        pygame.display.set_mode((800, 640), pygame.HWSURFACE|pygame.OPENGL|pygame.DOUBLEBUF)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                    self._mouse(event.button, event.type, *event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self._motion(*event.pos)
                elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    self._key(event.type, event.key)

            self._display()
            pygame.display.flip()
            self.timer.tick()
            time.sleep(0.03)

    def redraw(self):
        pass

    def _init(self):
        pygame.init()

    def _key(self, state, key):
        if state == pygame.KEYUP:
            self.event_handler.key_up(key)
        elif state == pygame.KEYDOWN:
            self.event_handler.key_down(key)

    def _mouse(self, button, state, x, y):
        if button == 4:
            self.event_handler.mouse_wheel(1)
        elif button == 5:
            self.event_handler.mouse_wheel(-1)
        else:
            pos = self._window_to_real(x, y)
            if state == pygame.MOUSEBUTTONUP:
                self.event_handler.mouse_up(button, pos)
            if state == pygame.MOUSEBUTTONDOWN:
                self.event_handler.mouse_down(button, pos)
        self.redraw()

    def _motion(self, x, y):
        self.event_handler.motion(self._window_to_real(x, y))
        self.redraw()

    def _window_to_real(self, x, y):
        return Vector2(x, y)

    def _mouse_wheel(self, button, dir, x, y):
        self.event_handler.mouse_wheel(dir)
        self.redraw()

    def _display(self):
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)

        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.2, 0.2, 0.2))

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-1, 1, -1, 1, 5, 5000)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glClear(GL_COLOR_BUFFER_BIT)

        glColor3f(0.0,0.0,0.0)
        glPushMatrix()

        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1))
        glLightfv(GL_LIGHT0, GL_POSITION, (20, 20, 20, 1))

        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)

        self.camera._setup()
        self._draw_obj(self.root)

        glPopMatrix()
        glFlush()

    def _draw_obj(self, obj):
        # bad procedular style - I wish Python support multimethods

        glPushMatrix()
        glTranslate(obj.pos.x, obj.pos.y, obj.pos.z)
        if obj.scale != 1:
            glScale(obj.scale, obj.scale, obj.scale)
        glMultMatrixd(obj.rotation.get_matrix()[:])

        if isinstance(obj, g3d.TriangleObject):
            TrianglesRenderer.get(obj).draw_content()
        elif isinstance(obj, g3d.Container):
            for item in obj.objects:
                self._draw_obj(item)
        else:
            raise TypeError(obj)

        glPopMatrix()

# ;;;;;;;;;;;;;;;;;;;; EVENTS ;;;;;;;;;;;;;;;;;;

RIGHT_BUTTON = 1
LEFT_BUTTON  = 3

class Keys:
    pass

Keys.__dict__.update(pygame.__dict__)

class EventHandler(object):
    def motion(self, pos):
        pass

    def mouse_down(self, button, pos):
        pass

    def mouse_up(self, button, pos):
        pass

    def mouse_wheel(self, dir):
        pass

    def key_up(self, key):
        pass

    def key_down(self, key):
        pass

# ;;;;;;;;;;;;;;;;;;; CAMERA ;;;;;;;;;;;;;;;;;;;

class Camera:
    def __init__(self):
        self.center = Vector3(0, 0, 0)
        self.eye = Vector3(2, 2, 2)
        self.up = Vector3(0, 1, 0)

    def _setup(self):
        GLU.gluLookAt(self.eye.x, self.eye.y, self.eye.z,
                      self.center.x, self.center.y, self.center.z,
                      self.up.x, self.up.y, self.up.z)


# ;;;;;;;;;;;;;;;;; RENDERERS ;;;;;;;;;;;;;;;;;;

class TrianglesRenderer:
    @classmethod
    def get(cls, triangles_object):
        if not hasattr(triangles_object, '_gl_renderer'):
            triangles_object._gl_renderer = cls(triangles_object.triangles)

        return triangles_object._gl_renderer

    def __init__(self, triangles):
        grouped_by_texture = []
        curr_group = None

        last_tex = Ellipsis
        for t in sorted(triangles, key=lambda t: t.texture):
            if t.texture != last_tex:
                curr_group = []
                grouped_by_texture.append((t.texture, curr_group))
                last_tex = t.texture
            curr_group.append(t)

        def sum_seq(it):
            acum = []
            for l in it:
                acum += l
            return acum

        self._grouped_by_texture = []
        for texture, triangles in grouped_by_texture:
            vertices = numpy.array(sum_seq([ [t.a[:], t.b[:], t.c[:]] for t in triangles ]))
            normals = numpy.array(sum_seq([ [t.na[:], t.nb[:], t.nc[:]] for t in triangles ]))
            uv = numpy.array(sum_seq([ [t.a_uv[:], t.b_uv[:], t.c_uv[:]] for t in triangles ]))
            assert len(vertices) == len(normals) == len(uv)
            self._grouped_by_texture.append((texture, normals, vertices, uv))

    def draw_content(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        for texture, normal, vertex, uv in self._grouped_by_texture:
            if g3d.options.enable_textures and texture:
                glBindTexture(GL_TEXTURE_2D, get_texture_id(texture))
            else:
                glBindTexture(GL_TEXTURE_2D, 0)

            glTexCoordPointer(2, GL_FLOAT, 0, uv)
            glNormalPointer(GL_FLOAT, 0, normal)
            glVertexPointer(3, GL_FLOAT, 0, vertex)
            glDrawArrays(GL_TRIANGLES, 0, len(vertex))

def get_texture_id(texture):
    if not hasattr(texture, '_gl_id'):
        w, h = texture.size
        texture._gl_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture._gl_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, 3, w, h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, texture.data)

    return texture._gl_id
