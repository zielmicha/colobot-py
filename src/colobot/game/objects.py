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

import colobot.game

objects = {}

def get(name):
    return objects[name]

def register_object(clazz):
    objects[clazz.__name__] = clazz
    return clazz

@register_object
class WheeledGrabber(colobot.game.Object):
    model = 'wheeled-transporter.model'

#@register_object
class Barrier1(colobot.game.Object):
    model = 'barrier1.model'
