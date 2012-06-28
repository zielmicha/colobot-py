import struct
import collections
import metafile
import functools
import Image
import g3d
from g3d import Vector3, Vector2

# ;;;;;;;;;;;;;;;; PUBLIC API ;;;;;;;;;;;;;;;;;

class Loader:
    '''
    Manages loading textures and .mod files from Colobot .dat files.
    '''
    def __init__(self):
        self.texture_cache = {}
        self.index = {}

    def add_modfile(self, path_or_modfile):
        ' Add content of Colobot .dat file to index. '
        if type(path_or_modfile) == str:
            f = metafile.MetaFile(metafile.cipher_keys['full'], open(path_or_modfile, 'rb'))
        else:
            f = path_or_modfile

        for key in f.entries:
            self.index[key] = functools.partial(f.open, key)

    def get_model(self, name):
        '''
        Loads model named `name` from index using self._load_model.
        '''
        return self._load_model(self.index[name]())

    def get_texture(self, name):
        '''
        Loads texture named `name` from index using self._load_texture.
        If texture was loaded yet, returns it from cache.
        '''
        if name not in self.texture_cache:
            input = self.index[name]()
            self.texture_cache[name] = self._load_texture(input)

        return self.texture_cache[name]

    def _load_texture(self, input):
        '''
        Creates GL texture from image supported by PIL and returns its g3d.TextureWrapper.
        '''
        im = Image.open(input)
        data = im.tostring('raw', 'RGBX', 0, -1)
        return g3d.create_rgbx_texture(data, im.size)
            
    def _load_model(self, input):
        '''
        Loads Colobot model from input and returns g3d.TriangleObject.
        Also loads and attaches textures.
        '''
        l = []
        for t in _load_modfile_data(input):
            texture = self.get_texture(t.tex_name)
            l.append(g3d.Triangle(
                    t.a, t.b, t.c, t.na, t.nb, t.nc, t.a_uv, t.b_uv, t.c_uv,
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
    
