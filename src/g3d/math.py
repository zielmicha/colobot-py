from __future__ import absolute_import
from euclid import Vector3, Vector2, Quaternion

from math import sin, cos, pi

# monkey-patch pyeuclid

def quaternion_inversed(self):
    m = abs(self * self.conjugated())
    return self.conjugated() * Quaternion(1. / m, 0, 0, 0)

Quaternion.inversed = quaternion_inversed
