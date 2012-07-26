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

import colobot.game.objects
from g3d.math import Vector2, Vector3, Quaternion, pi
import g3d.model

def load(lines, game):
    for title, args in parse(lines):
        method = globals().get('handle' + title)
        if method:
            method(game, **args)

def handleTerrainRelief(game, image, factor):
    HEIGHT_CONST = 80
    image = image.split('\\')[-1]
    texture = game.loader.get_texture(image)
    #game.terrain.texture = game.loader.get_texture('desert6.bmp')
    game.terrain.base_size = 368. * 2 / texture.size[0] # TODO: how Colobot/C++ handles this?
    game.terrain.load_from_relief(texture,
                                  height=factor * HEIGHT_CONST)

def handleCreateObject(game, pos, dir, type, cmdline=None, script1=None,
                       trainer=0, run=None, power=None, selectable=1,
                       clip=0, option=None, proxyActivate=0, proxyDistance=50):
    try:
        clazz = colobot.game.objects.get(type)
    except KeyError:
        return

    player = None
    model = g3d.model.read(loader=game.loader, name=clazz.model).clone()
    obj = clazz(game, model)
    obj.owner = player
    obj.position = Vector3(*pos)
    obj.rotation = get_rotation_quaternion(dir)
    game.add_object(obj)

def get_rotation_quaternion(dir):
    angle = (dir - 0.5) / 2 * pi
    return Quaternion.new_rotate_axis(angle, Vector3(0, 0, 1))

def parse(lines):
    for i, line in enumerate(lines):
        line = line.split('//')[0].strip()
        if not line:
            continue

        parts = _split_line(line)
        title = parts[0]
        args = {}

        new_parts = []
        for i in xrange(1, len(parts)):
            if '=' not in parts[i]:
                new_parts[-1] += parts[i]
            else:
                new_parts.append(parts[i])

        for part in new_parts:
            key, val = part.split('=', 1)
            try:
                args[key] = _parse_value(val)
            except SyntaxError:
                raise SyntaxError('line %d: %r' % (i+1, line))
        yield title, args

def _parse_value(val):
    if ';' in val:
        try:
            v = [ float(i.strip()) for i in val.split(';') ]
        except ValueError:
            raise SyntaxError(repr(val))
        if len(v) == 2:
            return Vector2(*v)
        elif len(v) == 3:
            return Vector3(*v)
        else:
            return tuple(v)
    try:
        return float(val)
    except ValueError:
        return val

def _split_line(line):
    '''
    Like line.split(), but preserves text in quatation marks and
    removes them.
    '''
    line += ' '
    parts = []
    current = []
    is_quoted = False
    for ch in line:
        if ch == '"':
            is_quoted = not is_quoted
        elif not is_quoted and ch in '\t ':
            if current:
                parts.append(''.join(current))
                current = []
        else:
            current.append(ch)

    if is_quoted:
        raise SyntaxError('unclosed quotation')

    return parts
