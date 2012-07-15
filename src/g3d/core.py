from __future__ import division
# RULE: do not modify vector unless you know that no one else will use it
from euclid import Vector3, Vector2, Quaternion
import collections
import time

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

class Timer:
    def __init__(self):
        self._intervals = []
        self._tickers = []
        self._last_tick = None

    def tick(self):
        current = time.time()
        for func in self._intervals:
            if func[1] > current:
                func[0]()
                func[1] += func[2]

        if self._last_tick:
            delta = current - self._last_tick
            for ticker in self._tickers:
                ticker(delta)

        self._last_tick = current
    
    def add_interval(self, interval, function):
        ''' Adds a function that will be called in regular intervals. '''
        self._functions.append([function, time.time() + interval, interval])

    def add_ticker(self, function):
        ''' Adds a function that will be called each tick with one argument - time elapsed from last call in seconds. '''
        self._tickers.append(function)
        
def wrap(obj):
    ' Wraps object with a container, so its position can be changed without modifing it. '
    c = Container()
    c.add(obj)
    return c



