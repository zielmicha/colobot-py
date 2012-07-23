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

import g3d
import g3d.model
import g3d.terrain

from g3d.math import Vector2, Vector3, Quaternion

import threading
import os

class Game(object):
    def __init__(self, loader):
        self.terrain = g3d.terrain.Terrain()
        self.loader = loader
        self.objects = []
        self.global_lock = threading.RLock()
        self.players = {}

        self.gravity = Vector3()

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
        obj.position = Vector3(5, 5, 20)
        obj.velocity = Vector3(4, 0, 0)
        self.objects.append(obj)

    def get_player_objects(self, player_name):
        return [ object for object in self.objects in object.player == self.get_player(player_name) ]

class Player(object):
    def __init__(self, game):
        self.game = game

class Object(object):
    def __init__(self, game, model):
        self.game = game
        self.ident = random_string()
        self.model = model
        self.owner = None

        self.position = Vector3()
        self.velocity = Vector3()

        self.rotation = Quaternion()
        self.angular_velocity = Quaternion()

        self.ground_area = Vector2(1, 1)

    def tick(self, time):
        # self.rotation *= self.angular_velocity ** time - TODO
        self.rotation = self.rotation.normalized()
        self.position += self.velocity * time # + (self.game.gravity * time ** 2) / 2
        #self.velocity += self.game.gravity * time

        self.check_ground()

    def check_ground(self):
        pass

def random_string(len=9):
    return os.urandom(len).encode('base64')[:len].replace('+', 'A').replace('/', 'B')
