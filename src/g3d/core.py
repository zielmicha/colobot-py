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
from __future__ import division
from g3d.math import Quaternion, Vector2, Vector3
import g3d.serialize
import collections
import time
import struct

Triangle = collections.namedtuple('Triangle',
                                  'a b c na nb nc a_uv b_uv c_uv texture')

MODULE_SERIAL_ID = 2

class options(object):
    enable_textures = True

class Object(object):
    def __init__(self):
        self.pos = Vector3()
        self.rotation = Quaternion()

    def clone(self, clone_dict=None):
        if clone_dict:
            clone_dict[self] = new

        obj = type(self)()
        obj.pos = self.pos
        obj.rotation = self.rotation
        return obj

@g3d.serialize.serializable
class TriangleObject(Object):
    def __init__(self, triangles):
        super(TriangleObject, self).__init__()

        self._triangles = triangles

    @property
    def triangles(self):
        return self._triangles

    def clone(self, clone_dict=None):
        if clone_dict:
            clone_dict[self] = new

        return self

    # ------------------------------

    serial_id = MODULE_SERIAL_ID, 1
    serial_separate = True

    _triangle_struct = '!' + ('fff' * 3) * 2 + ('ff' * 3)

    def _serialize(self):
        grouped_by_texture = []
        curr_group = None

        last_tex = Ellipsis
        for t in sorted(self._triangles, key=lambda t: t.texture):
            if t.texture != last_tex:
                curr_group = []
                grouped_by_texture.append((t.texture, curr_group))
                last_tex = t.texture
            curr_group.append(t)

        return [ (tex, self._serialize_triangles(triangles)) for tex, triangles in grouped_by_texture ]

    def _serialize_triangles(self, list):
        return ''.join( struct.pack(self._triangle_struct,
                             t.a.x, t.a.y, t.a.z, t.b.x, t.b.y, t.b.z, t.c.x, t.c.y, t.c.z,
                             t.na.x, t.na.y, t.na.z, t.nb.x, t.nb.y, t.nb.z, t.nc.x, t.nc.y, t.nc.z,
                             t.a_uv.x, t.a_uv.y, t.b_uv.x, t.b_uv.y, t.c_uv.x, t.c_uv.y) for t in list )

    @classmethod
    def _unserialize(self, x, y, z):
        return Vector3(x, y, z)

class Container(Object):
    def __init__(self):
        super(Container, self).__init__()
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)

    def remove(self, obj):
        self.objects.remove(obj)

    def clone(self, clone_dict=None):
        new = Object.clone(self, clone_dict)
        new.objects = [ obj.clone() for obj in self.objects ]
        return new

class Timer:
    def __init__(self):
        self._intervals = []
        self._tickers = []
        self._last_tick = None

    def tick(self):
        current = time.time()
        for func in self._intervals:
            if func[1] < current:
                func[0]()
                func[1] += func[2]

        if self._last_tick:
            delta = current - self._last_tick
            for ticker in self._tickers:
                ticker(delta)

        self._last_tick = current
    
    def add_interval(self, interval, function):
        ''' Adds a function that will be called in regular intervals (in seconds). '''
        self._intervals.append([function, time.time() + interval, interval])

    def add_ticker(self, function):
        ''' Adds a function that will be called each tick with one argument - time elapsed from last call in seconds. '''
        self._tickers.append(function)
        
def wrap(obj):
    ' Wraps object with a container, so its position can be changed without modifing it. '
    c = Container()
    c.add(obj)
    return c



