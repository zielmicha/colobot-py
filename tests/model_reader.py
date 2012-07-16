#!/usr/bin/python
import sys
import os
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import g3d.model.reader

class TestModelReader(unittest.TestCase):
    def test_parser(self):
        self.assertEqual(
g3d.model.reader._parse('''
# bleh
a
    b
    c
\td

e
f
   g
     h
'''),
            [('a', [('b', None), ('c', None), ('d', None)]), ('e', None), ('f', [('g', [('h', None)])])],
        )

        self.assertEqual(
g3d.model.reader._parse('''
# bleh
a
    b

    c
\td
\t\t
e
f
   g

     h
   i
'''),
            [('a', [('b', None), ('c', None), ('d', None)]), ('e', None), ('f', [('g', [('h', None)]), ('i', None)])],
        )
        
        self.assertRaises(IndentationError, g3d.model.reader._parse, 'a\n   b\n c')

if __name__ == '__main__':
    unittest.main()
