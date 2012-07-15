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
# Translation of metafile.(h|cpp) from C++ to Python

import sys
import struct
import StringIO

# from metafile.cpp
cipher_keys = {
    'full': [ 0x85, 0x91, 0x73, 0xcf, 0xa2, 0xbb, 0xf4, 0x77,
              0x58, 0x39, 0x37, 0xfd, 0x2a, 0xcc, 0x5f, 0x55,
              0x96, 0x90, 0x07, 0xcd, 0x11, 0x88, 0x21, ]
}

class CryptingFile:
    def __init__(self, key, file):
        self.file = file
        self.key = key
        self.i = 0

    def seek(self, n):
        self.i = n % len(self.key)
        self.file.seek(n)
        
    def read(self, n=2**30, noenc=False):
        block = self.file.read(n)
        if noenc:
            self.i += len(block)
            return block
        ret = []
        length = len(self.key)
        for ch in block:
            ret.append(chr(self.key[self.i] ^ ord(ch)))
            self.i = (self.i + 1) % length
        return ''.join(ret)

    def read_unpack(self, code, noenc=False):
        size = struct.calcsize(code)
        return struct.unpack(code, self.read(size, noenc=noenc))

class MetaFile:
    def __init__(self, key, file):
        self.file = CryptingFile(key, file)
        size, = self.file.read_unpack('i', noenc=True)
        self.entries = {}
        
        for name, start, length in [ self.file.read_unpack('14sii') for i in xrange(size) ]:
            self.entries[name.rstrip('\0')] = (start, length)

    def read(self, name):
        start, length = self.entries[name]
        self.file.seek(start)
        return self.file.read(length)

    def open(self, name):
        return StringIO.StringIO(self.read(name))

if __name__ == '__main__':
    import sys
    name = 'colobot.data/colobot2.dat' if not sys.argv[1:] else sys.argv[1]
    f = MetaFile(cipher_keys['full'], open(name))

    for key in f.entries.keys():
        print key
    #print len(f.read('keyc.mod'))

    #print f.entries['keyc.mod']
    #print repr(f.read('keyc.mod')[:100])

#while True:
    

    
