#!/usr/bin/python
import sys
import os
import unittest
import StringIO

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import colobot.modfile

from g3d import Vector2, Vector3
from colobot.modfile import _Triangle as Triangle

class TestLoader(unittest.TestCase):
    
    def test_loading_success(self):
        loader = colobot.modfile.Loader()
        loader.add_directory('data/models')
        loader.add_directory('data/diagram')
        loader.add_directory('data/textures')
        
        self.assertTrue(loader.get_model('keya.mod'))
        self.assertTrue(loader.get_model('keyb.mod'))
        self.assertTrue(loader.get_model('home1.mod'))
        self.assertRaises(KeyError, loader.get_model, 'blehblehbleh.mod')
        self.assertRaises(KeyError, loader.get_model, 'keya')

    def test_disabled_textures(self):
        loader = colobot.modfile.Loader(enable_textures=False)
        loader.add_directory('data/models')
        
        self.assertTrue(loader.get_model('keya.mod'))
        self.assertTrue(loader.get_model('keyb.mod'))
        self.assertTrue(loader.get_model('home1.mod'))
        self.assertRaises(KeyError, loader.get_model, 'blehblehbleh.mod')
        self.assertRaises(KeyError, loader.get_model, 'keya')

class TestReader(unittest.TestCase):
    keya_data = '''
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
'''.decode('base64')
    keya_result = [Triangle(a=Vector3(1.40, 0.00, 0.00), b=Vector3(-0.70, 0.00, 1.21), c=Vector3(0.00, 0.00, 0.00), na=Vector3(0.00, -1.00, 0.00), nb=Vector3(0.00, -1.00, 0.00), nc=Vector3(0.00, -1.00, 0.00), a_uv=Vector2(0.39, 0.12), b_uv=Vector2(0.42, 0.12), c_uv=Vector2(0.39, 0.12), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(-0.70, 0.00, 1.21), b=Vector3(-0.70, 0.00, -1.21), c=Vector3(0.00, 0.00, 0.00), na=Vector3(-0.00, -1.00, 0.00), nb=Vector3(-0.00, -1.00, 0.00), nc=Vector3(-0.00, -1.00, 0.00), a_uv=Vector2(0.42, 0.12), b_uv=Vector2(0.37, 0.12), c_uv=Vector2(0.39, 0.12), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(-0.70, 0.00, -1.21), b=Vector3(1.40, 0.00, 0.00), c=Vector3(0.00, 0.00, 0.00), na=Vector3(0.00, -1.00, -0.00), nb=Vector3(0.00, -1.00, -0.00), nc=Vector3(0.00, -1.00, -0.00), a_uv=Vector2(0.37, 0.12), b_uv=Vector2(0.39, 0.12), c_uv=Vector2(0.39, 0.12), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(1.40, 2.00, 0.00), b=Vector3(-0.70, 2.00, 1.21), c=Vector3(1.40, 0.00, 0.00), na=Vector3(0.50, -0.00, 0.87), nb=Vector3(0.50, -0.00, 0.87), nc=Vector3(0.50, -0.00, 0.87), a_uv=Vector2(0.37, 0.00), b_uv=Vector2(0.42, 0.00), c_uv=Vector2(0.37, 0.12), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(-0.70, 2.00, 1.21), b=Vector3(-0.70, 0.00, 1.21), c=Vector3(1.40, 0.00, 0.00), na=Vector3(0.50, 0.00, 0.87), nb=Vector3(0.50, 0.00, 0.87), nc=Vector3(0.50, 0.00, 0.87), a_uv=Vector2(0.42, 0.00), b_uv=Vector2(0.42, 0.12), c_uv=Vector2(0.37, 0.12), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(-0.70, 2.00, 1.21), b=Vector3(-0.70, 2.00, -1.21), c=Vector3(-0.70, 0.00, 1.21), na=Vector3(-1.00, 0.00, 0.00), nb=Vector3(-1.00, 0.00, 0.00), nc=Vector3(-1.00, 0.00, 0.00), a_uv=Vector2(0.42, 0.00), b_uv=Vector2(0.37, 0.00), c_uv=Vector2(0.42, 0.12), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(-0.70, 2.00, -1.21), b=Vector3(-0.70, 0.00, -1.21), c=Vector3(-0.70, 0.00, 1.21), na=Vector3(-1.00, 0.00, 0.00), nb=Vector3(-1.00, 0.00, 0.00), nc=Vector3(-1.00, 0.00, 0.00), a_uv=Vector2(0.37, 0.00), b_uv=Vector2(0.37, 0.12), c_uv=Vector2(0.42, 0.12), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(-0.70, 2.00, -1.21), b=Vector3(1.40, 2.00, 0.00), c=Vector3(-0.70, 0.00, -1.21), na=Vector3(0.50, 0.00, -0.87), nb=Vector3(0.50, 0.00, -0.87), nc=Vector3(0.50, 0.00, -0.87), a_uv=Vector2(0.37, 0.00), b_uv=Vector2(0.42, 0.00), c_uv=Vector2(0.37, 0.12), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(1.40, 2.00, 0.00), b=Vector3(1.40, 0.00, 0.00), c=Vector3(-0.70, 0.00, -1.21), na=Vector3(0.50, 0.00, -0.87), nb=Vector3(0.50, 0.00, -0.87), nc=Vector3(0.50, 0.00, -0.87), a_uv=Vector2(0.42, 0.00), b_uv=Vector2(0.42, 0.12), c_uv=Vector2(0.37, 0.12), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(-0.70, 2.00, 1.21), b=Vector3(1.40, 2.00, 0.00), c=Vector3(0.00, 2.00, 0.00), na=Vector3(0.00, 1.00, -0.00), nb=Vector3(0.00, 1.00, -0.00), nc=Vector3(0.00, 1.00, -0.00), a_uv=Vector2(0.42, 0.00), b_uv=Vector2(0.39, 0.00), c_uv=Vector2(0.39, 0.00), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(-0.70, 2.00, -1.21), b=Vector3(-0.70, 2.00, 1.21), c=Vector3(0.00, 2.00, 0.00), na=Vector3(0.00, 1.00, 0.00), nb=Vector3(0.00, 1.00, 0.00), nc=Vector3(0.00, 1.00, 0.00), a_uv=Vector2(0.37, 0.00), b_uv=Vector2(0.42, 0.00), c_uv=Vector2(0.39, 0.00), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1),
 Triangle(a=Vector3(1.40, 2.00, 0.00), b=Vector3(-0.70, 2.00, -1.21), c=Vector3(0.00, 2.00, 0.00), na=Vector3(-0.00, 1.00, 0.00), nb=Vector3(-0.00, 1.00, 0.00), nc=Vector3(-0.00, 1.00, 0.00), a_uv=Vector2(0.39, 0.00), b_uv=Vector2(0.37, 0.00), c_uv=Vector2(0.39, 0.00), tex_name='vegetal.tga', min=0.0, max=1000000.0, state=0, tex_num=1)]
    
    def test_loading_keya(self):
        result = list(colobot.modfile._load_modfile_data(StringIO.StringIO(self.keya_data)))
        self.assertEqual(repr(result), repr(self.keya_result)) # need to compare repr, because it's generally not good idea to compare floats
