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

import math
import g3d
import g3d.model

from g3d import Vector2, Vector3, Quaternion

def read(loader, name):
    model = g3d.model.Model()
    read_into(loader, name, model, model.root)
    return model

def read_into(loader, name, model, group):
    data = loader.read_file(name)
    _load_group(loader, _parse(data), model, group)

def _load_group(loader, tree, model, group):
    if not tree:
        return

    def handle_part():
        model_name, name, translate, rotate, scale = \
            _get_options(options, 'model', 'name', 'translate', 'rotate', 'scale')
        obj = g3d.wrap(loader.get_model(model_name))
        group.add(obj)
        _bind_trans(obj, translate, rotate, scale)
        if name:
            model.objects[name] = obj

    def handle_include():
        name, = _get_options(options, 'name')
        read_into(loader, name, model, group)

    def handle_group():
        name, translate, rotate, scale = \
            _get_options(options, 'name', 'translate', 'rotate', 'scale')
        obj = g3d.Container()
        _bind_trans(obj, translate, rotate, scale)
        _load_group(loader, children, model, obj)
        group.add(obj)
        if name:
            model.objects[name] = obj

    def handle_animation():
        name, = _get_options(options, 'name')
        animation = g3d.model.AnimationGroup()
        model.animations[name] = animation
        _load_anim(loader, children, model, animation)

    def assert_no_children():
        if children:
            raise SyntaxError('command %s shouldn\'t have any children' % command)

    for item, children in tree:
        command, options = _parse_line(item)

        if command == 'include':
            assert_no_children()
            handle_include()
        elif command == 'part':
            assert_no_children()
            handle_part()
        elif command == 'group':
            handle_group()
        elif command == 'animation':
            handle_animation()
        else:
            raise SyntaxError('invalid command %s' % command)

def _load_anim(loader, tree, model, animation):
    def assert_no_children():
        if children:
            raise SyntaxError('command %s shouldn\'t have any children' % command)

    for item, children in tree:
        command, options = _parse_line(item)

        if command == 'interpolate_to':
            assert_no_children()
            name, rotate, start, speed, time = _get_options(options, 'name', 'rotate',
                                                            'start', 'speed', 'time')
            speed = float(speed) if speed else None
            speed = speed * math.pi / 180
            time = float(time) if time else None
            start = float(start or 0.0)
            rotate = _parse_rotate(rotate)
            anim = g3d.model.InterpolateRotation(model.objects[name], rotate, speed=speed, time=time)
            animation.add(start=start, animation=anim)
        else:
            raise SyntaxError('invalid command %s' % command)

def _float_list(s):
    if not s:
        return [0., 0., 0.]
    return map(float, s.split(','))

def _bind_trans(obj, translate, rotate, scale):
    obj.pos = Vector3(*_float_list(translate))
    obj.rotation = _parse_rotate(rotate)
    obj.scale = float(scale) if scale else 1

def _parse_rotate(s):
    rotate = _float_list(s)
    if len(rotate) == 4: # around axis
        return Quaternion.new_rotate_axis(rotate[0] / 180. * math.pi,
                                                  Vector3(*vector[1:]))
    else:
        x, y, z = [ i / 180. * math.pi for i in rotate ]
        return Quaternion.new_rotate_euler(y, z, x)

def _get_options(options, *names):
    for key in options:
        if key not in names:
            raise SyntaxError('invalid option name %s' % key)

    return [ options.get(name) for name in names ]

def _parse_line(text):
    parts = text.split()
    command = parts[0]
    options = {}
    for part in parts[1:]:
        if '=' not in part:
            raise SyntaxError(text)
        name, value = part.split('=', 1)
        if name in options:
            raise SyntaxError(text)
        options[name] = value

    return command, options

def _parse(data):
    # normalize whitespace
    data = data.replace('\t', ' ' * 4)
    lines = data.splitlines()

    root = []
    groups_by_level = {0: root}
    current_level = 0
    for line in lines:
        if '#' in line:
            line = line.split('#', 1)[0]
        line = line.rstrip()
        if not line.strip():
            continue
        spaces_count = len(line) - len(line.lstrip(' '))
        line = line.strip()
        if spaces_count < current_level:
            if spaces_count not in groups_by_level:
                raise IndentationError
            # remove all groups with greater level
            for level in groups_by_level.keys():
                if level > spaces_count:
                    del groups_by_level[level]
            groups_by_level[spaces_count].append(line)
            current_level = spaces_count
        elif spaces_count == current_level:
            groups_by_level[spaces_count].append(line)
        else:
            group = []
            groups_by_level[spaces_count] = group
            groups_by_level[current_level].append(group)
            group.append(line)
            current_level = spaces_count

    return _pair_captions(root)

def _pair_captions(l):
    if isinstance(l[0], list):
        raise IndentationError

    out = []
    i = 1
    while i <= len(l):
        if i < len(l) and isinstance(l[i], list):
            assert not isinstance(l[i-1], list)
            out.append((l[i-1], _pair_captions(l[i])))
            i += 1
        else:
            out.append((l[i-1], None))
        i += 1
    return out

if __name__ == '__main__':
    import os
    import sys
    data_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'anim')
    import g3d.loader
    loader = g3d.loader.Loader()
    loader.add_directory(data_path)

    model = read(loader, sys.argv[1])
    print model
