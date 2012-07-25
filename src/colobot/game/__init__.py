# Copyright (C) 2012, Michal Zielinski <michal@zielinscy.org.pl>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import division

import g3d
import g3d.model
import g3d.terrain

from g3d.math import Vector2, Vector3, Quaternion, atan, pi

import threading
import logging
import os

class Game(object):
    def __init__(self, loader):
        self.terrain = Terrain()
        self.loader = loader
        self.objects_by_id = {}
        self.global_lock = threading.RLock()
        self.players = {}

        self.gravity = Vector3(0, 0, -20)
        self._static_num = 0

    @property
    def objects(self):
        return self.objects_by_id.itervalues()

    def get_player(self, name):
        if name not in self.players:
            self.players[name] = Player(self)
        return self.players[name]

    def load_terrain(self, name):
        file = self.loader.index[name]()
        self.terrain.load_from_relief(file)

    def tick(self, time):
        with self.global_lock:
            for obj in self.objects:
                obj.tick(time)

    def get_objects(self):
        with self.global_lock:
            return list(self.objects)

    def create_static_object(self, player_name, name):
        # for debugging
        player = self.get_player(player_name)
        model = g3d.model.read(loader=self.loader, name=name).clone()
        obj = Object(self, model)
        obj.owner = player
        obj.position = Vector3(120, 135 + self._static_num * 30, 210)
        obj.velocity = Vector3(40, 0, 0)
        obj.rotation = Quaternion.new_rotate_axis(0, Vector3(0, 0, 1))
        self._static_num += 1
        self.objects_by_id[obj.ident] = obj

    def get_player_objects(self, player_name):
        return [ object for object in self.objects
                 if object.player == self.get_player(player_name) ]

    def motor(self, player_name, bot_id, motor):
        object = self.objects_by_id[bot_id]
        if self.get_player(player_name) != object.owner:
            raise NotAuthorizedError()
        object.motor = motor

class NotAuthorizedError(Exception):
    ''' Raised when player tries to access robot of other player. '''

class Player(object):
    def __init__(self, game):
        self.game = game

class Object(object):
    def __init__(self, game, model):
        self.game = game
        self.ident = random_string()
        self.model = model
        self.owner = None

        self.is_on_ground = False

        self.position = Vector3()
        self.velocity = Vector3()

        self.rotation = Quaternion()
        self.angular_velocity = Vector3()

        self.mass = 1

        self.motor = (0, 0)
        self.motor_force = 1
        self.motor_radius = 1

    def tick(self, time):
        if abs(self.angular_velocity) > 0.001:
            q = Quaternion.new_rotate_axis(abs(self.angular_velocity) * 0.01,
                                       self.angular_velocity.normalized())
        else:
            q = Quaternion()
        self.rotation *= q
        self.rotation = self.rotation.normalized()
        self.position += self.velocity * time + (self.game.gravity * time ** 2) / 2
        self.velocity += self.game.gravity * time

        self.calc_motor(time)
        self.check_ground(time)

    def calc_motor(self, time):
        f0, f1 = self.motor
        f = f0 + f1 # net force
        m = (f1 - f0) / self.motor_radius # torque
        self.velocity += self.rotation * Vector3(f / self.mass, 0, 0)
        j = self.mass # moment of intertia
        self.angular_velocity += (m / j) *  Vector3(0, 0, 1)

    def check_ground(self, time):
        center = Vector2(self.position.x, self.position.y)
        height = self.game.terrain.get_height_at(center)
        if self.position.z <= height:
            if not self.is_on_ground:
                logging.debug('dups!')
            self.is_on_ground = True
            self.position.z = height

            self.adjust_rotation(center, height)
            self.rotate_velocity(center, height)
            self.apply_friction(time)
        else:
            if self.is_on_ground:
                logging.debug('up!')
            self.is_on_ground = False

    def adjust_rotation(self, center, height):
        # y, z, x
        heading, attitude, bank = self.rotation.get_euler()

        height_x = self.game.terrain.get_height_at(center + Vector2(1, 0))
        heading = -atan(height_x - height)

        height_y = self.game.terrain.get_height_at(center + Vector2(0, 1))
        bank = atan(height_y - height)

        # TODO: use angular_velocity instead
        d_rotation = Quaternion.new_rotate_euler(heading, attitude, bank)

        self.rotation = d_rotation

    def rotate_velocity(self, center, height):
        ''' Make sure that velocity is not pointed underground. '''
        velocity_projection = Vector2(self.velocity.x, self.velocity.y)
        if abs(velocity_projection) < 0.001:
            return
        velocity_projection = velocity_projection.normalized()
        height_v = self.game.terrain.get_height_at(center + velocity_projection)
        ground_vector = Vector3(velocity_projection.x, velocity_projection.y, height_v - height).normalized()
        velocity_angle = Vector3.angle_between(ground_vector, self.velocity)
        if velocity_angle < 0:
            self.velocity = abs(self.velocity) * self.ground_vector

    def apply_friction(self, time):
        kinetic_friction = \
            self.game.terrain.get_kinetic_friction(self.position, self.velocity) * time
        if kinetic_friction > abs(self.velocity):
            self.velocity = Vector3(0, 0, 0)
        else:
            self.velocity -= (self.velocity.normalized() * kinetic_friction)

        angular_friction = \
            self.game.terrain.get_angular_friction(self.position,
                                                   self.angular_velocity) * time

        if abs(self.angular_velocity) < angular_friction:
            self.angular_velocity = Vector3()
        else:
            self.angular_velocity -= self.angular_velocity.normalized() * angular_friction

class Terrain(g3d.terrain.Terrain):
    def __init__(self):
        super(Terrain, self).__init__()

    def get_kinetic_friction(self, pos, velocity):
        ' Returns value of linear deacceleration caused by friction. '
        return abs(velocity) * 3 # arbitrary constant

    def get_angular_friction(self, pos, angular_velocity):
        return 9 # arbitrary constant

def random_string(len=9):
    return os.urandom(len).encode('base64')[:len].replace('+', 'A').replace('/', 'B')
