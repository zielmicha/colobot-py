import sys
import os
import unittest
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from g3d.math import *

class TestMath(unittest.TestCase):
    def test_inverse(self):
        l = [(1, 0, 0, 0),
             (0, 1, 0, 0),
             (0.01, 1, 1, 0)]
        for item in l:
            self.check_inverse(Quaternion(*item))
        self.assertRaises(ZeroDivisionError, Quaternion(0).inversed)

    def test_inverse_random(self):
        for i in xrange(1000):
            q = Quaternion(random.random(), random.random(), random.random(), random.random())
            self.check_inverse(q)
    
    def check_inverse(self, q):
        self.assertQuaternionEqual(Quaternion(1, 0, 0, 0), q * q.inversed())

    def assertQuaternionEqual(self, a, b):
        self.assertAlmostEqual(a.w, b.w)
        self.assertAlmostEqual(a.x, b.x)
        self.assertAlmostEqual(a.y, b.y)
        self.assertAlmostEqual(a.z, b.z)
