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

''' Interface inspired on PyEuclid, but it is on GPL. '''

from __future__ import absolute_import, division

import g3d.serialize

from math import sin, cos, pi, acos, asin, tan, atan, atan2, e, log, ceil as _ceil

MODULE_SERIAL_ID = 1

floor = int

def ceil(i):
    return int(_ceil(i))

def safe_asin(a):
    if a > 1:
        a = 1
    elif a < -1:
        a = -1
    return asin(a)

@g3d.serialize.serializable
class Vector2(object):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def normalized(self):
        l = abs(self)
        return Vector2(self.x / l, self.y / l)

    def __abs__(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __eq__(self, o):
        if not isinstance(o, Vector2):
            return False
        return self.x == o.x and self.y == o.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other):
        assert isinstance(other, Vector2)
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        assert isinstance(other, Vector2)
        return Vector2(self.x - other.x, self.y - other.y)

    def __repr__(self):
        return 'Vector2(%.2f, %.2f)' % (self.x, self.y)

    def __iter__(self):
        return iter([self.x, self.y])

    def __mul__(self, other):
        assert isinstance(other, (float, int, long))
        return Vector2(self.x * other, self.y * other)

    __rmul__ = __mul__

    def __div__(self, other):
        assert isinstance(other, (float, int, long))
        return Vector2(self.x / other, self.y / other)

    __truediv__ = __div__

    def __getitem__(self, i):
        return [self.x, self.y][i]

    serial_id = MODULE_SERIAL_ID, 1
    serial_struct = 'ff'

    def _serialize(self):
        return (self.x, self.y)

    @classmethod
    def _unserialize(self, x, y):
        return Vector2(x, y)

@g3d.serialize.serializable
class Vector3(object):
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def normalized(self):
        l = abs(self)
        return Vector3(self.x / l, self.y / l, self.z / l)

    def cross(self, other):
        return Vector3(self.y * other.z - self.z * other.y,
                       self.z * other.x - self.x * other.z,
                       self.x * other.y - self.y * other.x)

    def __mul__(self, a):
        assert isinstance(a, (float, int, long))
        return Vector3(self.x * a, self.y * a, self.z * a)

    __rmul__ = __mul__

    def __div__(self, a):
        assert isinstance(a, (float, int, long))
        return Vector3(self.x / a, self.y / a, self.z / a)

    __truediv__ = __div__

    def __eq__(self, o):
        if not isinstance(o, Vector3):
            return False
        return self.x == o.x and self.y == o.y and self.z == o.z

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __repr__(self):
        return 'Vector3(%.2f, %.2f, %.2f)' % (self.x, self.y, self.z)

    def __add__(self, other):
        assert isinstance(other, Vector3)
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        assert isinstance(other, Vector3)
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __abs__(self):
        return (self.x**2 + self.y**2 + self.z**2)**0.5

    def __iter__(self):
        return iter([self.x, self.y, self.z])

    def __getitem__(self, i):
        return [self.x, self.y, self.z][i]

    @staticmethod
    def angle_between(a, b):
        return asin(abs(a.normalized().cross(b.normalized())))

    serial_id = MODULE_SERIAL_ID, 2
    serial_struct = 'fff'

    def _serialize(self):
        return (self.x, self.y, self.z)

    @classmethod
    def _unserialize(self, x, y, z):
        return Vector3(x, y, z)

@g3d.serialize.serializable
class Quaternion(object):
    def __init__(self, w=1, x=0, y=0, z=0):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return 'Quaternion(real=%.2f, imag=<%.2f, %.2f, %.2f>)' % (
            self.w, self.x, self.y, self.z)

    def get_matrix(self):
        xx = self.x * self.x
        xy = self.x * self.y
        xz = self.x * self.z
        xw = self.x * self.w

        yy = self.y * self.y
        yz = self.y * self.z
        yw = self.y * self.w

        zz = self.z * self.z
        zw = self.z * self.w

        tmp = [  # that's in row major
                 1 - 2 * (yy + zz),  # a
                 2 * (xy - zw),      # b
                 2 * (xz + yw),      # c
                 0,                  # d
                 2 * (xy + zw),      # e
                 1 - 2 * (xx + zz),  # f
                 2 * (yz - xw),      # g
                 0,                  # h
                 2 * (xz - yw),      # i
                 2 * (yz + xw),      # j
                 1 - 2 * (xx + yy),  # k
                 0,  # l
                 0,  # m
                 0,  # n
                 0,  # o
                 1,  # p
                 ]
        # and in column major that opengl wants
        return [tmp[0], tmp[4], tmp[8], tmp[12],
                tmp[1], tmp[5], tmp[9], tmp[13],
                tmp[2], tmp[6], tmp[10], tmp[14],
                tmp[3], tmp[7], tmp[11], tmp[15]]

    def get_angle_axis(self):
        # vec[z] >= 0
        q = self.normalized()
        angle1 = 2 * acos(q.w)
        angle2 = (1 - q.w ** 2) ** 0.5
        if angle2 < 0.001:
            return 0, Vector3(1, 0, 0)
        vec = Vector3(q.x / angle2, q.y / angle2, q.z / angle2)
        if vec.z < 0:
            vec *= -1
            angle1 *= -1
            angle1 %= 2 * pi
        return angle1, vec

    @classmethod
    def from_vector3(self, vec):
        return Quaternion(0, vec.x, vec.y, vec.z)

    def to_vector3(self):
        return Vector3(self.x, self.y, self.z)

    def normalized(self):
        l = abs(self)
        return Quaternion(self.w/l, self.x/l, self.y/l, self.z/l)

    def conjugated(self):
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def inversed(self):
        m = abs(self * self.conjugated())
        return self.conjugated() * Quaternion(1. / m, 0, 0, 0)

    def __add__(self, other):
        assert isinstance(other, Quaternion)
        return Quaternion(self.w + other.w,
                          self.x + other.x,
                          self.y + other.y,
                          self.z + other.z)

    def __sub__(self, other):
        assert isinstance(other, Quaternion)
        return Quaternion(self.w - other.w,
                          self.x - other.x,
                          self.y - other.y,
                          self.z - other.z)

    def __mul__(self, other):
        if isinstance(other, Quaternion):
            return Quaternion(
                -self.x * other.x - self.y * other.y
                -self.z * other.z + self.w * other.w,
                +self.x * other.w + self.y * other.z
                -self.z * other.y + self.w * other.x,
                -self.x * other.z + self.y * other.w
                +self.z * other.x + self.w * other.y,
                +self.x * other.y - self.y * other.x
                +self.z * other.w + self.w * other.z)
        elif isinstance(other, Vector3):
            w, x, y, z = self
            X, Y, Z = other
            return Vector3(w * w * X + 2 * y * w * Z -
                           2 * z * w * Y + x * x * X +
                           2 * y * x * Y + 2 * z * x * Z -
                           z * z * X - y * y * X,

                           2 * x * y * X + y * y * Y +
                           2 * z * y * Z + 2 * w * z * X -
                           z * z * Y + w * w * Y -
                           2 * x * w * Z - x * x * Y,

                           2 * x * z * X + 2 * y * z * Y +
                           z * z * Z - 2 * w * y * X -
                           y * y * Z + 2 * w * x * Y -
                           x * x * Z + w * w * Z)
        elif isinstance(other, (float, int, long)):
            return Quaternion(self.w * other,
                              self.x * other,
                              self.y * other,
                              self.z * other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (float, int, long)):
            return Quaternion(self.w * other,
                              self.x * other,
                              self.y * other,
                              self.z * other)
        else:
            return NotImplemented

    def __pow__(self, exp):
        if (self.x ** 2 + self.y ** 2 + self.z ** 2) < 0.001:
            return Quaternion(self.w ** exp)
        return (self.ln() * exp).exp()

    def exp(self):
        a = self.w
        vec = self.to_vector3()
        norm = abs(vec)
        if norm < 0.001:
            return Quaternion(e ** a)
        return (e ** a) * (Quaternion(cos(norm)) +
                           Quaternion.from_vector3(vec / norm) * sin(norm))

    def ln(self):
        self_norm = abs(self)
        a = self.w
        vec = self.to_vector3()
        norm = abs(vec)
        if norm < 0.001:
            return Quaternion(log(a))
        return Quaternion(log(self_norm), 0, 0, 0) \
            + Quaternion.from_vector3(vec / norm) * acos(a / self_norm)

    def __abs__(self):
        return (self.x**2 + self.y**2 + self.z**2 + self.w**2) ** 0.5

    def __iter__(self):
        return iter([self.w, self.x, self.y, self.z])

    def get_euler(self):
        # http://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
        # http://www.euclideanspace.com/maths/geometry/rotation/conversions/quaternionToEuler/
        w, x, y, z = self
        test = x*y + z*w
        if test > 0.499:
            heading = 2 * atan2(x, w)
            attitude = pi/2
            bank = 0
        elif test < -0.499:
            heading = -2 * atan2(x, w)
            attitude = -pi/2
            bank = 0
        else:
            sqx = x*x
            sqy = y*y
            sqz = z*z
            heading = atan2(2*y*w-2*x*z, 1 - 2*sqy - 2*sqz)
            attitude = asin(2*test)
            bank = atan2(2*x*w-2*y*z, 1 - 2*sqx - 2*sqz)

        if abs(heading) + 0.001 >= pi:
            # Does it work?
            heading += pi
            bank += pi
            attitude = pi - attitude

        heading %= 2 * pi
        bank %= 2 * pi
        attitude %= 2 * pi

        return heading, attitude, bank

    @classmethod
    def new_rotate_axis(cls, angle, axis):
        axis = axis.normalized()
        Sin = sin(angle / 2)
        Cos = cos(angle / 2)
        return Quaternion(Cos, axis.x * Sin, axis.y * Sin, axis.z * Sin)

    @classmethod
    def new_rotate_euler(cls, heading, attitude, bank):
        Hc = cos(heading / 2)
        Hs = sin(heading / 2)
        Ac = cos(attitude / 2)
        As = sin(attitude / 2)
        Bc = cos(bank / 2)
        Bs = sin(bank / 2)

        return cls(Hc * Ac * Bc - Hs * As * Bs,
                   Hs * As * Bc + Hc * Ac * Bs,
                   Hs * Ac * Bc + Hc * As * Bs,
                   Hc * As * Bc - Hs * Ac * Bs)

    @classmethod
    def angle_between(cls, q1, q2):
        q1 = q1.normalized()
        q2 = q2.normalized()

        dot = q1.w * q2.w + q1.x * q2.x + q1.y * q2.y + q1.z * q2.z
        if dot > 0.9995:
            return q1 + t * (q1 - q2)

        if dot < 0:
            # we don't want to rotate "the longer way"
            q1 = q1.conjugated()
            dot *= -1

        if dot > 1:
            # or acos may raise MathError
            dot = 1

        return acos(dot)

    @classmethod
    def new_interpolate(cls, q1, q2, t):
        # http://number-none.com/product/Understanding%20Slerp,%20Then%20Not%20Using%20It/
        q1 = q1.normalized()
        q2 = q2.normalized()

        dot = q1.w * q2.w + q1.x * q2.x + q1.y * q2.y + q1.z * q2.z
        if dot > 0.9995:
            return q1 + t * (q1 - q2)

        if dot < 0:
            # we don't want to rotate "the longer way"
            q1 = q1.conjugated()
            dot *= -1

        if dot > 1:
            # or acos may raise MathError
            dot = 1

        theta_0 = acos(dot)
        theta = theta_0 * t
        q3 = (q2 - q1 * dot).normalized()

        return q1 * cos(theta) + q3 * sin(theta)

    serial_id = MODULE_SERIAL_ID, 3
    serial_struct = 'ffff'

    def _serialize(self):
        return (self.w, self.x, self.y, self.z)

    @classmethod
    def _unserialize(self, w, x, y, z):
        return Quaternion(w, x, y, z)
