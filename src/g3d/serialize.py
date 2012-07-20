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
'''
Serializer is designer to transmit models thought network.
Unlike traditional picklers, g3d.serializer allows caching - larger object
like models are not transmitted inline, but instead their SHA1 is embedded.

Serializer doesn't work magically like pickle - all classes need to marked
as serializable and provide _serialize and _unserialized methods.
'''

import struct as _struct # do not use directly
import hashlib
import collections
import StringIO

serializables_by_id = {}
serializables_by_type = {}

def pack(code, *args):
    return _struct.pack('!' + code, *args)

def serializable(clazz):
    add_serializable_class(clazz, clazz)
    return clazz

def serializer_for(for_type):
    def method(clazz):
        add_serializable_class(clazz, for_type)
        return clazz
    
    return method

def sha1(data):
    return hashlib.sha1(data).digest()

def add_serializable_class(clazz, for_type):
    if clazz.serial_id in serializables_by_id:
        raise RuntimeError('id collision: %s and %s' % (clazz, serializables_by_id[clazz.serial_id]))
    serializables_by_id[clazz.serial_id] = clazz
    serializables_by_type[for_type] = clazz

MODULE_BUILTIN = 0
ID_SHA1 = 1

SHA1_LENGTH = 20

class Serializer(object):
    def __init__(self):
        self.objects = IdDict()
        self.deps = IdDict()
        self.serialized_by_sha1 = {}

    def add(self, object):
        data = self.serialize(object, no_separate=True)
        id = sha1(data)
        self.objects[object] = id
        self.serialized_by_sha1[id] = data
        return id

    def get_dependencies(self, object):
        return [ item for item in self.deps.get(object, [])
                 if item != self.objects[object] ]
    
    def get_by_sha1(self, sha1):
        return self.serialized_by_sha1[sha1]
    
    def serialize(self, object, no_separate=False):
        to = StringIO.StringIO()
        self.serialize_to(to, object, no_separate=no_separate)
        return to.getvalue()
    
    def serialize_to(self, out, object, no_separate=False):
        serializer = self._get_serializer(object)
        separate = getattr(serializer, 'serial_separate', False)

        if not no_separate and separate:
            out.write( pack('HH', MODULE_BUILTIN, ID_SHA1) )
            id = self.add(object)
            assert len(id) == SHA1_LENGTH
            self.deps.setdefault(object, []).append(id)
            out.write( id )
        else:
            out.write( pack('HH', *serializer.serial_id) )
            self._serialize_content(out, serializer, object)
    
    def _serialize_content(self, out, serializer, object):
        if issubclass(serializer, IterableSerializer):
            self._serialize_iterable(out, object)
        else:
            result = serializer._serialize(object)
            struct_code = getattr(serializer, 'serial_struct', Ellipsis)

            if struct_code == Ellipsis:
                self.serialize_to(out, result)
                self.extend_dep(object, result)
            elif struct_code:
                out.write( pack(struct_code, *result) )
            elif struct_code == None:
                out.write( pack('I', len(result)) )
                out.write(result)
                
    def _serialize_iterable(self, out, object):
        l = list(object)
        out.write( pack('I', len(l)) )
        for item in l:
            self.serialize_to(out, item)
            self.extend_dep(object, item)

    def extend_dep(self, object, src_object):
        self.deps.setdefault(object, []).extend( self.deps.get(src_object, []) )
                
    def _get_serializer(self, object):
        return serializables_by_type[object.__class__]
    
class IdDict(object):
    def __init__(self):
        self._data = {}

        # make sure that keys are not garbage collected
        self._alive_keeper = {} 

    def __setitem__(self, key, item):
        self._alive_keeper[id(key)] = key
        self._data[id(key)] = item

    def __getitem__(self, key):
        try:
            return self._data[id(key)]
        except KeyError:
            raise KeyError(key)

    def setdefault(self, key, data):
        if id(key) not in self._data:
            self[key] = data
        return self[key]

    def get(self, key, default=None):
        if id(key) not in self._data:
            return default
        return self[key]
    
class IterableSerializer:
    ''' Implemented in Serializer. '''
    
@serializer_for(list)
class ListSerializer(IterableSerializer):
    serial_id = MODULE_BUILTIN, 2
    iter_class = list

@serializer_for(tuple)
class TupleSerializer(IterableSerializer):
    serial_id = MODULE_BUILTIN, 3
    iter_class = tuple

@serializer_for(int)
class IntSerializer:
    serial_id = MODULE_BUILTIN, 4
    serial_struct = 'i'

    @staticmethod
    def _serialize(self):
        return (self, )

    @staticmethod
    def _unserialize(data):
        return data

@serializer_for(str)
class StrSerializer:
    serial_id = MODULE_BUILTIN, 5
    serial_struct = None
    
    @staticmethod
    def _serialize(self):
        return self

    @staticmethod
    def _unserialize(data):
        return data
    
if __name__ == '__main__':
    import g3d
    import g3d.gl
    import g3d.camera_drivers
    import g3d.model
    import g3d.serialize
    import colobot.loader

    loader = colobot.loader.Loader(enable_textures=True)
    loader.add_directory('data/models')
    loader.add_directory('data/anim')
    loader.add_directory('data/diagram')
    loader.add_directory('data/textures')

    #g3d.model.read(loader=loader, name='wheeled-transporter.model')
    model = loader.get_model('keya.mod')
    
    s = g3d.serialize.Serializer()
    sha1 = s.add(model)
    print sha1.encode('hex')
    data = s.get_by_sha1(sha1)
    import zlib
    print len(data), len(zlib.compress(data))
    print s.deps[model]
