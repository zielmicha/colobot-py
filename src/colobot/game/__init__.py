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

from g3d.math import Vector2, Vector3, Quaternion, atan, safe_asin, pi
import g3d.serialize

import threading
import logging
import os

MODULE_SERIAL_ID = 101

class Game(object):
    def __init__(self, loader):
        self.terrain = Terrain()
        self.loader = loader
        self.objects_by_id = {}
        self.global_lock = threading.RLock()
        self.players = {}

        self.gravity = Vector3(0, 0, -12)
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

    def load_scene(self, name):
        import colobot.game.scene_file # TODO
        with self.global_lock:
            file = self.loader.index[name]()
            colobot.game.scene_file.load(file, self)

    def tick(self, time):
        with self.global_lock:
            for obj in self.objects:
                obj.tick(time)

    def get_objects(self):
        with self.global_lock:
            return list(self.objects)

    def create_static_object(self, player_name, name, pos=None):
        # for debugging
        player = self.get_player(player_name)
        model = g3d.model.read(loader=self.loader, name=name).clone()
        obj = Object(self, model)
        obj.owner = player
        obj.position = pos or Vector3(120, 135 + self._static_num * 30, 210)
        obj.rotation = Quaternion.new_rotate_axis(0, Vector3(0, 0, 1))
        model.root.scale = 10
        self._static_num += 1
        self.add_object(obj)

    def add_object(self, obj):
        self.objects_by_id[obj.ident] = obj

    def get_player_objects(self, player_name):
        return [ object for object in self.objects
                 if object.owner == self.get_player(player_name) ]

    def motor(self, player_name, bot_id, motor):
        object = self.objects_by_id[bot_id]
        #if self.get_player(player_name) != object.owner:
        #    raise NotAuthorizedError()
        object.motor = motor

class NotAuthorizedError(Exception):
    ''' Raised when player tries to access robot of other player. '''

class Player(object):
    def __init__(self, game):
        self.game = game

class Object(object):
    model_scale = 0.2
    probe_len = 0.1

    def __init__(self, game, model):
        self.game = game
        self.ident = random_string()
        self.model = model
        self.model.root.scale = self.model_scale
        self.owner = None

        self.is_on_ground = False

        self.position = Vector3()
        self.velocity = Vector3()

        self.rotation = Quaternion()
        self.angular_velocity = Vector3()

        self.motor = (0, 0)

    def tick(self, time):
        if abs(self.angular_velocity) > 0.001:
            q = Quaternion.new_rotate_axis(abs(self.angular_velocity) * time,
                                       self.angular_velocity.normalized())
        else:
            q = Quaternion()
        self.rotation *= q
        self.rotation = Quaternion.new_rotate_axis(*self.rotation.get_angle_axis())
        self.position += self.velocity * time + (self.game.gravity * time ** 2) / 2
        self.velocity += self.game.gravity * time

        self.check_ground(time)

    def calc_motor(self, time):
        f0, f1 = self.motor
        f = (f0 + f1) * self.motor_force # net force
        m = (f1 - f0) * self.motor_force * self.motor_radius # torque
        self.velocity += self.rotation * Vector3(f / self.mass * time, 0, 0)
        j = self.mass # moment of intertia
        self.angular_velocity += (m / j * time) *  Vector3(0, 0, 1)

    def check_ground(self, time):
        center = Vector2(self.position.x, self.position.y)
        height = self.game.terrain.get_height_at(center)
        if self.position.z <= height:
            self.is_on_ground = True
            self.position.z = height

            self.calc_motor(time)
            #self.adjust_rotation(center, height)
            #self.rotate_velocity(center, height)
            self.apply_friction(time)
        else:
            self.is_on_ground = False

    def adjust_rotation(self, center, height):
        probe_len = 1#self.probe_len
        # y, z, x
        heading, attitude, bank = self.rotation.get_euler()

        height_x = self.game.terrain.get_height_at(center + Vector2(probe_len, 0))
        heading = -safe_asin((height_x - height) / probe_len)

        height_y = self.game.terrain.get_height_at(center + Vector2(0, probe_len))
        bank = safe_asin((height_y - height) / probe_len)

        # TODO: use angular_velocity instead
        d_rotation = Quaternion.new_rotate_euler(heading, 0, bank)
        d_rotation *= Quaternion.new_rotate_euler(0, attitude, 0)

        self.rotation = d_rotation

    def rotate_velocity(self, center, height):
        ''' Make sure that velocity is not pointed underground. '''
        velocity_projection = Vector2(self.velocity.x, self.velocity.y)
        if abs(velocity_projection) < 0.001:
            return
        velocity_projection = velocity_projection.normalized()
        height_v = self.game.terrain.get_height_at(center + velocity_projection)
        ground_vector = Vector3(velocity_projection.x,
                                velocity_projection.y,
                                height_v - height).normalized()
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

@g3d.serialize.serializable
class Terrain(g3d.terrain.Terrain):
    def __init__(self):
        super(Terrain, self).__init__()

    def get_kinetic_friction(self, pos, velocity):
        ' Returns value of linear deacceleration caused by friction. '
        return abs(velocity) * 10 # arbitrary constant

    def get_angular_friction(self, pos, angular_velocity):
        return 10 # arbitrary constant

    # ----------------------

    serial_id = MODULE_SERIAL_ID, 1


def random_string(len=9):
    return os.urandom(len).encode('base64')[:len].replace('+', 'A').replace('/', 'B')
