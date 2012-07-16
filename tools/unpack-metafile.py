#!/usr/bin/python
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import metafile

if len(sys.argv) != 3:
    sys.exit('Usage: unpack-metafile.py metafile output-dir')

path, output = sys.argv[1:]

f = metafile.MetaFile(metafile.cipher_keys['full'], open(path))

if not os.path.isdir(output):
    os.mkdir(output)


for name in f.entries:
    output_path = os.path.join(output, name)
    print name, '->', output_path
    data = f.read(name)
    with open(output_path, 'wb') as outp:
        outp.write(data)
