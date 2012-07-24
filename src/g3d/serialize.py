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
import logging

serializables_by_id = {}
serializables_by_type = {}

def pack(code, *args):
    return _struct.pack('!' + code, *args)

def unpack(code, data):
    return _struct.unpack('!' + code, data)

def calcsize(code):
    return _struct.calcsize('!' + code)

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
        self.objects_by_sha1 = {}
        self.deps = IdDict()
        self.serialized_by_sha1 = {}

    def add(self, object):
        data = self.serialize(object, no_separate=True)
        id = sha1(data)
        self.objects[object] = id
        self.serialized_by_sha1[id] = data
        self.objects_by_sha1[id] = object
        return id

    def get_dependencies_by_sha1(self, sha1):
        return self.get_dependencies(self.objects_by_sha1[sha1])

    def get_dependencies(self, object):
        if type(object) == str and len(object) == SHA1_LENGTH:
            logging.warn('get_dependencies on something that looks like sha1')
        ' Returns SHA1 of dependencies '
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

class Unserializer(object):
    def __init__(self, cache=None):
        self.cache = cache or {}
        self.loaded = {}

    def add(self, sha1, data):
        self.cache[sha1] = data

    def load(self, sha1):
        if sha1 not in self.loaded:
            try:
                data = self.cache[sha1]
            except KeyError:
                raise ObjectNotAddedError(sha1)
            input = StringIO.StringIO(data)
            obj = self.load_from(input)
            self.loaded[sha1] = obj

        return self.loaded[sha1]

    def load_from(self, input):
        def safe_call(serializer, args):
            try:
                return serializer._unserialize(*args)
            except TypeError as err:
                logging.error('when calling _unserialize of %s: %s', serializer, err)
                raise

        id = unpack('HH', input.read(4))
        if id == (MODULE_BUILTIN, ID_SHA1):
            return self.load(input.read(SHA1_LENGTH))
        else:
            serializer = self._get_serializer(id)
            if issubclass(serializer, IterableSerializer):
                size, = unpack('I', input.read(4))
                l = [ self.load_from(input) for i in xrange(size) ]
                return serializer.iter_class(l)
            else:
                struct = getattr(serializer, 'serial_struct', Ellipsis)
                if struct == None:
                    size, = unpack('I', input.read(4))
                    return serializer._unserialize(input.read(size))
                elif struct == Ellipsis:
                    return safe_call(serializer, self.load_from(input))
                else:
                    size = calcsize(struct)
                    params = unpack(struct, input.read(size))
                    return safe_call(serializer, params)

    def _get_serializer(self, id):
        return serializables_by_id[id]

class ObjectNotAddedError(Exception):
    ' Raised when required object is not added. '
    def __init__(self, sha1):
        Exception.__init__(self, sha1.encode('hex'))
        self.sha1 = sha1

class DiskCache(object):
    ' Dictionary that stores its contest in directory '
    def __init__(self, path):
        raise NotImplementedError

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

class PrimitiveSerializer:
    @staticmethod
    def _serialize(self):
        return (self, )

    @staticmethod
    def _unserialize(data):
        return data

@serializer_for(int)
class IntSerializer(PrimitiveSerializer):
    serial_struct = 'i'
    serial_id = MODULE_BUILTIN, 4

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

@serializer_for(float)
class FloatSerializer(PrimitiveSerializer):
    serial_struct = 'd'
    serial_id = MODULE_BUILTIN, 6

@serializer_for(type(None))
class NoneSerializer:
    serial_struct = ''
    serial_id = MODULE_BUILTIN, 7

    @staticmethod
    def _serialize(self):
        return ()

    @staticmethod
    def _unserialize():
        return None

@serializer_for(dict)
class NoneSerializer:
    serial_id = MODULE_BUILTIN, 8

    @staticmethod
    def _serialize(self):
        return (self.items(), )

    @staticmethod
    def _unserialize(seq):
        return dict(seq)

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
    sha1hash = s.add(model)
    print sha1hash.encode('hex')
    data = s.get_by_sha1(sha1hash)
    import zlib
    print len(data), len(zlib.compress(data))
    print [ i.encode('hex') for i in s.deps[model] ]
    print [ i.encode('hex') for i in s.get_dependencies(model) ]

    uns = g3d.serialize.Unserializer()
    uns.add(sha1hash, data)
    for hash in s.get_dependencies(model):
        data = s.get_by_sha1(hash)
        uns.add(hash, data)
    out = uns.load(sha1hash)
