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

import g3d
import Image

from g3d import Vector2, Vector3

class Terrain(object):
    def __init__(self, base_size=0.1):
        self.base_size = base_size
        self.heights = []
        self.model = None

    def load_from_relief(self, file, height=2):
        im = Image.open(file)
        pix = im.load()
        for x in xrange(im.size[0]):
            row = []
            self.heights.append(row)
            for y in xrange(im.size[1]):
                val = pix[x, y]
                row.append(val * height / 256)
        self._update_model()

    def _update_model(self):
        def _get(x, y):
            height = (self.heights[y])[x]
            return Vector3(x * self.base_size, y * self.base_size, height)

        def _create_triangle(a, b, c):
            normal = (a - b).cross(c - a).normalized()
            nil = Vector2()
            return g3d.Triangle(a, b, c, normal, normal, normal, nil, nil, nil, None)
        
        triangles = []
        for y in xrange(0, len(self.heights) - 1):
            row = self.heights[y]
            for x in xrange(0, len(row) - 1):
                a = _get(x, y)
                b = _get(x + 1, y)
                c = _get(x, y + 1)
                d = _get(x + 1, y + 1)

                # order is important - or normals will be inverted
                triangles.append(_create_triangle(c, b, a))
                triangles.append(_create_triangle(c, d, b))

        self.model = g3d.TriangleObject(triangles)

    
