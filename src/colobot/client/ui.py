#!/usr/bin/python
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
import g3d.terrain
import g3d.gl
import g3d.camera_drivers

import colobot.client

from g3d.math import Vector2, Vector3, Quaternion

class UIWindow(object):
    def __init__(self, client, game_name):
        self.client = client
        self.terrain = g3d.terrain.Terrain()
        self.game_name = game_name
        self.update_reader = colobot.client.UpdateReader(
            client, client.open_update_channel(game_name))

        self.root = g3d.Container()
        self.objects_by_id = {}

    def setup(self):
        heights = self.client.get_terrain(self.game_name)
        self.terrain.set_heights(heights)

    def loop(self):
        win = g3d.gl.Window()
        win.timer.add_ticker(self.tick)
        win.root.add(self.terrain.model)
        win.root.add(self.root)
        CameraDriver(self).install(win)
        #g3d.camera_drivers.TopCameraDriver().install(win)

        win.loop()

    def tick(self, _):
        # TODO: interpolate
        data = self.update_reader.get_new_updates()
        if not data:
            return

        server_time, new, deleted, updates = data
        for ident, model in new:
            self.objects_by_id[ident] = model.clone()
            self.root.add(self.objects_by_id[ident].root)

        for ident in deleted:
            model = self.objects_by_id[ident]
            del self.objects_by_id[ident]
            self.root.remove(model.root)

        for ident, position, velocity, rotation, angular_velocity in updates:
            obj = self.objects_by_id[ident]
            obj.root.pos = position
            obj.root.rotation = rotation

class CameraDriver(g3d.camera_drivers.CameraDriver):
    def __init__(self, window):
        super(CameraDriver, self).__init__()
        self.camera.up = Vector3(0, 0, 1)
        self.window = window
        self._object = None
        self._ordered_objects = []

        self.dist_behind = 240.
        self.dist_above = 120.

    def install(self, window):
        super(CameraDriver, self).install(window)
        window.timer.add_ticker(self.tick)

    def tick(self, delta):
        if not self._object:
            if self.window.objects_by_id: # FIXME: race condition
                self._get_next_object()
            pass # top view
        else:
            heading, attitude, bank = self._object.root.rotation.get_euler()
            attitude_q = Quaternion.new_rotate_euler(0, attitude * 2, 0) # why *2 ??
            vec = attitude_q * Vector3(1, 0, 0)
            self.camera.eye = self._object.root.pos - (vec * self.dist_behind
                                                       ) + Vector3(0, 0, self.dist_above)
            self.camera.center = self._object.root.pos

    def key_down(self, key):
        if key == g3d.gl.Keys.K_TAB:
            self._get_next_object()

    def _get_next_object(self):
        current = set(self.window.objects_by_id.values())
        current_index = (self._ordered_objects.index(self._object)
                         if self._object in self._ordered_objects else -1)
        self._ordered_objects = [ o for o in self._ordered_objects if o in current ]
        if len(self._ordered_objects) != len(current):
            old = set(self._ordered_objects)
            for o in current:
                if o not in old:
                    self._ordered_objects.append(o)

        if not self._ordered_objects:
            self._object = None
        else:
            index = (current_index + 1) % len(self._ordered_objects)
            self._object = self._ordered_objects[index]
