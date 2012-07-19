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

class UIWindow(object):
    def __init__(self, client, game_name):
        self.client = client
        self.terrain = g3d.terrain.Terrain()
        self.game_name = game_name

    def setup(self):
        heights = self.client.get_terrain(self.game_name)
        self.terrain.set_heights(heights)

    def loop(self):
        win = g3d.gl.Window()
        win.root.add(self.terrain.model)
        g3d.camera_drivers.FreeCameraDriver().install(win)
        
        win.loop()
    
    
