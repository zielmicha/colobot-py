from __future__ import division
# RULE: do not modify vector unless you know that no one else will use it
from euclid import Vector3, Vector2, Quaternion
import collections

Triangle = collections.namedtuple('Triangle',
                                  'a b c na nb nc a_uv b_uv c_uv texture')

class options(object):
    enable_textures = True

class Object(object):
    def __init__(self):
        self.pos = Vector3()

class TriangleObject(Object):
    def __init__(self, triangles):
        super(TriangleObject, self).__init__()

        self._triangles = triangles

    @property
    def triangles(self):
        return self._triangles

class Container(Object):
    def __init__(self):
        super(Container, self).__init__()
        self.objects = []
    
    def _draw_content(self):
        for obj in self.objects:
            obj._draw()

    def add(self, obj):
        self.objects.append(obj)

    def remove(self, obj):
        self.objects.remove(obj)

def wrap(obj):
    ' Wraps object with a container, so its position can be changed without modifing it. '
    c = Container()
    c.add(obj)
    return c



