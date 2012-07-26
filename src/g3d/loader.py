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
import os
import gzip
import functools
import pygame

import g3d

class Loader(object):
    def __init__(self, enable_textures=True):
        self.enable_textures = enable_textures
        self.index = {}
        self.texture_cache = {}
        self.model_cache = {}

    def add_directory(self, path):
        ' Add content of directory to index. '
        for name in os.listdir(path):
            if name.endswith('.gz'):
                func = functools.partial(gzip.open,
                                         os.path.join(path, name),
                                         'rb')
                name = name[:-3]
            else:
                func = functools.partial(open,
                                         os.path.join(path, name),
                                         'rb')
            self.index[name] = func

    def read_file(self, name):
        return self.index[name]().read()

    def get_model(self, name):
        '''
        Loads model named `name` from index using self._load_model.
        '''
        if name not in self.model_cache:
            self.model_cache[name] = self._load_model(self.index[name]())

        return self.model_cache[name]

    def get_texture(self, name):
        '''
        Loads texture named `name` from index using self._load_texture.
        If texture was loaded yet, returns it from cache.
        Returns None if texture loading is disabled.
        '''
        if not self.enable_textures:
            return None

        if name not in self.texture_cache:
            input = self.index[self._find_texture(name)]()
            self.texture_cache[name] = self._load_texture(input)

        return self.texture_cache[name]

    def _find_texture(self, name):
        if name in self.index:
            return name

        raise KeyError(name)

    def _load_texture(self, input):
        '''
        Creates GL texture from image supported by Pygame and
        returns its g3d.TextureWrapper.
        '''
        im = pygame.image.load(input)
        data = pygame.image.tostring(im, 'RGBX', True)
        return g3d.create_rgbx_texture(data, im.get_size())

    def _load_model(self, input):
        ''' Loads model from input and returns g3d.TriangleObject
        - should be overriden by subclasses. '''
        raise NotImplementedError('should be overriden by subclass')
