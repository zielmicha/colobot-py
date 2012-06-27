import struct
import collections

Triangle = collections.namedtuple('Triangle',
                                  'a b c na nb nc a_uv b_uv c_uv tex_name min max state tex_num')

# from modfile.h and modfile.cpp
struct_InfoMOD = 'iii10i'
# anyone knows why it worked when I add "8x" after each "8f"?
#   looks like there are two float which are not in d3dtypes.h
struct_ModelTriangle = '??8f8x8f8x8f8x68x20sffihhhh' # material - 17f - 68x

def load_modfile(input):
    rev, vers, total, _, _, _, _, _, _, _, _, _, _ = read_unpack(input, struct_InfoMOD)

    if rev != 1 or vers not in (1, 2):
        raise ValueError('unsupported rev %d vers %d' % (rev, vers))

    for i in xrange(total):
        b_used, b_select, \
            p1_x, p1_y, p1_z, p1_nx, p1_ny, p1_nz, p1_u, p1_v, \
            p2_x, p2_y, p2_z, p2_nx, p2_ny, p2_nz, p2_u, p2_v, \
            p3_x, p3_y, p3_z, p3_nx, p3_ny, p3_nz, p3_u, p3_v, \
            tex_name, min, max, state, tex_num_2, \
            _, _, _ \
            = read_unpack(input, struct_ModelTriangle)

        tex_name = strip_c_string(tex_name)
        
        yield Triangle(
            (p1_x, p1_y, p1_z), (p2_x, p2_y, p2_z), (p3_x, p3_y, p3_z),
            (p1_nx, p1_ny, p1_nz), (p2_nx, p2_ny, p2_nz), (p3_nx, p3_ny, p3_nz),
            (p1_u, p1_v), (p2_u, p2_v), (p3_u, p3_v), state=state,
            tex_name=tex_name, min=min, max=max, tex_num=tex_num_2,
            )

    left = len(input.read())
    if left:
        raise ValueError('garbage at the end of file (%d, %.2f per entry, entry size = %d)'
                         % (left, float(left)/total, struct.calcsize(struct_ModelTriangle)))

def strip_c_string(s):
    if '\0' not in s:
        return s
    else:
        return s[:s.find('\0')]
    
def read_unpack(f, code):
    size = struct.calcsize(code)
    return struct.unpack(code, f.read(size))
    
if __name__ == '__main__':
    import metafile

    f = metafile.MetaFile(metafile.cipher_keys['full'], open('colobot.data/colobot2.dat'))

    print list(sorted(f.entries))
    
    for key in f.entries:
        inp = f.open(key)
        load_modfile(inp)
    
