import sys
import os
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import hashlib

import g3d
import g3d.gl
import g3d.camera_drivers
import g3d.model
import g3d.serialize
import colobot.loader

class TestSerialize(unittest.TestCase):
    def setUp(self):
        self.loader = colobot.loader.Loader(enable_textures=True)
        self.loader.add_directory('data/models')
        self.loader.add_directory('data/anim')
        self.loader.add_directory('data/diagram')
        self.loader.add_directory('data/textures')

    def test_serialize_model(self):
        model = self.loader.get_model('keya.mod')

        s = g3d.serialize.Serializer()
        sha1 = s.add(model)
        self.assertEqual( sha1.encode('hex'), 'e1608989565054047629390ae10ac3f917cc3953' )

        self.assertEqual( hashlib.sha1(s.get_by_sha1(sha1)).digest(), sha1 )
        self.assertEqual( s.get_dependencies(model), ['\x17,XO\xc6\xcd=T\xe0!\x184+P?\x03!\xb5\xc1\xc3'] )

if __name__ == '__main__':
    unittest.main()
