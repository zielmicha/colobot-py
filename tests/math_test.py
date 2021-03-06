import sys
import os
import unittest
import random
import euclid

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from g3d.math import *

class TestQuaternion(unittest.TestCase):
    # TODO: create much more tests

    def test_op(self):
        self.assertAlmostEqual(Quaternion(1, 1, 1, 1).__abs__(), 2)
        self.assertAlmostEqual(Quaternion(5, 0, 0, 0).__abs__(), 5)

    def test_if_quaternions_behave_as_they_should(self):
        q = Quaternion()
        # rotate (21/20)*pi
        for i in xrange(21):
            q *= Quaternion.new_rotate_axis(pi / 10, Vector3(0, 0, 1))

        self.assertAlmostEqual(q.get_angle_axis()[0], pi / 10)

        q = Quaternion()
        # rotate (21/20)*pi
        for i in xrange(100):
            q *= Quaternion.new_rotate_axis(pi / 40, Vector3(0, 0, 1))
            print q.get_euler(), pi / 40 * (i + 1), q * Vector3(1, 0, 0)
            self.assertAnglesEqual(q.get_euler()[1], pi / 40 * (i + 1))

    def assertAnglesEqual(self, a, b):
        delta = (a - b) % (2 * pi)
        ellipsis = 0.00001
        self.assertTrue(delta < ellipsis or (2 * pi - delta) < ellipsis,
                        msg="%r doesn't equal %r" % (a, b))

    def test_get_angle_axis(self):
        l = [Quaternion(1, 1, 1, 1), Quaternion(5, 0, 0, 0),
             Quaternion.new_rotate_euler(pi / 2, 0, 0),
             Quaternion(0.1, 2, 3, 4), Quaternion(0.01, 1, 1, 0)]
        for i in xrange(100):
            l.append(Quaternion(random.random(), random.random(),
                                random.random(), random.random()))
        for q in l:
            q = q.normalized()
            angle, axis = q.get_angle_axis()
            q2 = q.new_rotate_axis(angle, axis)
            self.assertQuaternionEqual(q2, q)

    def test_power(self):
        l = [Quaternion(1, 1, 1, 1), Quaternion(5, 0, 0, 0),
             Quaternion.new_rotate_euler(pi / 2, 0, 0),
             Quaternion(0.1, 2, 3, 4), Quaternion(0.01, 1, 1, 0)]
        for q in l:
            q = q.normalized()
            self.assertQuaternionEqual(q * q, q ** 2)
            self.assertQuaternionEqual(q * q * q, q ** 3)
            self.assertQuaternionEqual(q * q * q * q * q, q ** 5)
            self.assertQuaternionEqual((q ** 0.1) * (q ** 0.9), q)

    def test_get_euler(self):
        l = [Quaternion(1, 1, 1, 1), Quaternion(5, 0, 0, 0),
             Quaternion.new_rotate_euler(pi / 2, 0, 0)]
        for q in l:
            q = q.normalized()
            euler = q.get_euler()
            q2 = Quaternion.new_rotate_euler(*euler)
            self.assertQuaternionEqual(q, q2)

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

    def test_get_matrix(self):
        self.check_get_matrix((1, 1, 1, 0))
        self.check_get_matrix((0, 1, 1, 0))
        self.check_get_matrix((0, 0, 0, 0))

        for i in xrange(1000):
            q = (random.random(), random.random(), random.random(), random.random())
            self.check_get_matrix(q)

    def check_get_matrix(self, tpl):
        q1 = Quaternion(*tpl)
        q2 = euclid.Quaternion(*tpl)
        m1 = q1.get_matrix()[:]
        m2 = q2.get_matrix()[:]

        for i, a1, a2 in zip(xrange(16), m1, m2):
            self.assertAlmostEqual(a1, a2, msg='component %s' % 'abcdefghijklmnop'[i])

    def check_inverse(self, q):
        self.assertQuaternionEqual(Quaternion(1, 0, 0, 0), q * q.inversed())

    def assertQuaternionEqual(self, a, b):
        self.assertAlmostEqual(a.w, b.w)
        self.assertAlmostEqual(a.x, b.x)
        self.assertAlmostEqual(a.y, b.y)
        self.assertAlmostEqual(a.z, b.z)

class TestVector(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(Vector3(1, 1, 1), Vector3(1, 1, 1))
        self.assertEqual(hash(Vector3(1, 1, 1)), hash(Vector3(1, 1, 1)))
