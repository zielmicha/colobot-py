# Copyright (C) 2012, Michal Zielinski <michal@zielinscy.org.pl>
# Copyright (C) 2001-2008, Daniel ROUX & EPSITEC SA, www.epsitec.ch
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
#
# Translation of modfile.(h|cpp) from C++ to Python

import struct
import collections
import pygame
import g3d
import g3d.loader
from g3d import Vector3, Vector2

# ;;;;;;;;;;;;;;;; PUBLIC API ;;;;;;;;;;;;;;;;;

class Loader(g3d.loader.Loader):
    '''
    Manages loading textures and Colobot .mod files.
    '''
    def __init__(self):
        super(Loader, self).__init__()
            
    def _find_texture(self, name):
        if name in self.index:
            return name
        # original Colobot are .tga and .bmp files, but .png is better
        if name.endswith(('.tga', '.bmp')) and (name[:-4] + '.png') in self.index:
            return name[:-4] + '.png'

        raise KeyError(name)
        
    def _load_model(self, input):
        '''
        Loads Colobot model from input and returns g3d.TriangleObject.
        Also loads and attaches textures.
        '''
        l = []

        def _uv((u, v)):
            return Vector2(u, 1 - v)
        
        for t in _load_modfile_data(input):
            if t.tex_name:
                texture = self.get_texture(t.tex_name)
            else:
                texture = None
            l.append(g3d.Triangle(
                    t.a, t.b, t.c, t.na, t.nb, t.nc, _uv(t.a_uv), _uv(t.b_uv), _uv(t.c_uv),
                    texture=texture
            ))
        return g3d.TriangleObject(l)

# ;;;;;;;;;;;;;;; IMPLEMENTATION ;;;;;;;;;;;;;;;

_Triangle = collections.namedtuple('Triangle',
                                  'a b c na nb nc a_uv b_uv c_uv tex_name '
                                  'min max state tex_num')

# from modfile.h and modfile.cpp
struct_InfoMOD = 'iii10i'
# anyone knows why it worked when I add "8x" after each "8f"?
#   looks like there are two float which are not in d3dtypes.h
struct_ModelTriangle = '??8f8x8f8x8f8x68x20sffihhhh' # material - 17f - 68x

def _load_modfile_data(input):
    rev, vers, total, _, _, _, _, _, _, _, _, _, _ = _read_unpack(input, struct_InfoMOD)

    if rev != 1 or vers not in (1, 2):
        raise ValueError('unsupported rev %d vers %d' % (rev, vers))

    for i in xrange(total):
        b_used, b_select, \
            p1_x, p1_y, p1_z, p1_nx, p1_ny, p1_nz, p1_u, p1_v, \
            p2_x, p2_y, p2_z, p2_nx, p2_ny, p2_nz, p2_u, p2_v, \
            p3_x, p3_y, p3_z, p3_nx, p3_ny, p3_nz, p3_u, p3_v, \
            tex_name, min, max, state, tex_num_2, \
            _, _, _ \
            = _read_unpack(input, struct_ModelTriangle)

        tex_name = _strip_c_string(tex_name)

        V3=Vector3; V2=Vector2
        
        yield _Triangle(
            V3(p1_x, p1_y, p1_z), V3(p2_x, p2_y, p2_z), V3(p3_x, p3_y, p3_z),
            V3(p1_nx, p1_ny, p1_nz), V3(p2_nx, p2_ny, p2_nz), V3(p3_nx, p3_ny, p3_nz),
            V2(p1_u, p1_v), V2(p2_u, p2_v), V2(p3_u, p3_v),
            state=state,
            tex_name=tex_name, min=min, max=max, tex_num=tex_num_2,
        )

    left = len(input.read())
    if left:
        raise ValueError('garbage at the end of file (%d, %.2f per entry, entry size = %d)'
                         % (left, float(left)/total, struct.calcsize(struct_ModelTriangle)))
    
def _strip_c_string(s):
    if '\0' not in s:
        return s
    else:
        return s[:s.find('\0')]
    
def _read_unpack(f, code):
    size = struct.calcsize(code)
    return struct.unpack(code, f.read(size))
    
if __name__ == '__main__':
    import metafile

    f = metafile.MetaFile(metafile.cipher_keys['full'], open('colobot.data/colobot2.dat'))

    print list(sorted(f.entries))
    
    for key in f.entries:
        inp = f.open(key)
        load_modfile(inp)
    
