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

class StaticObject(colobot.game.Object):
    selectable = False

    mass = 9999999
    motor_force = 0
    motor_radius = 0

class Building(StaticObject):
    selectable = True

class Transportable(StaticObject):
    selectable = False

class Bot(colobot.game.Object):
    selectable = True

    mass = 1
    motor_force = 50
    motor_radius = 0.5

# -----------------------------

@register_object
class WheeledGrabber(Bot):
    model = 'wheeled-transporter.model'

# ---------------------------

@register_object
class Barrier1(StaticObject):
    model = 'barrier1.model'

# ----------------------------

@register_object
class BotFactory(Building):
    model = 'factory.model'

@register_object
class ResearchCenter(Building):
    model = 'research.model'

@register_object
class Portico(Building):
    model = 'portico.model'

@register_object
class Houston(Building):
    model = 'houston.model'

# --------------------------

@register_object
class Titanium(Transportable):
    model = 'titanium.model'

@register_object
class PowerCell(Transportable):
    model = 'power-cell.model'
