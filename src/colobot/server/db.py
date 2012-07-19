# Copyright (C) 2012, Michal Zielinski <michal@zielinscy.org.pl>
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

import os
import json
import string
import threading
import hashlib

class NotFoundError(Exception): pass

def locked(method):
    ''' Decorator that behaves like `with self.profile.lock` '''
    def decorated(self, *args, **kwargs):
        with self.lock:
            method(self, *args, **kwargs)
    functools.wraps(decorated, method)
    
    return decorated

def sha256(text):
    return hashlib.sha256(text).hexdigest()

class ProfileEntry:
    def __init__(self, profile, *args):
        self.profile = profile
        self.file = profile.storage.get(*args, **{'default': self.default})

class Dict(ProfileEntry):
    default = {}
    def __getattr__(self, name):
        return self.file.data[name]
        
class List(ProfileEntry):
    default = []
    entry_cls = lambda self, x, y: y
    def get_by(self, attrib, value):
        for entry in self.file.data:
            if entry[attrib] == value:
                return self.entry_cls(self.profile, entry)
        raise NotFoundError('%s.get_by(%r, %r)' % (self.__class__.__name__, attrib, value))

# ;;;;;;;;;;;;;;;;;;;;;;;;;;;;; low level ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    
allowed_chars = string.digits + string.ascii_letters + '-_+=.,'

class File(object):
    def __init__(self, path, default=[]):
        self.path = path
        try:
            f = open(path)
            self.data = json.load(f)
        except IOError:
            self.data = default

    def write(self):
        _overwrite(self.path, json.dumps(self.data))

def join(*args):
    if not args:
        return ''
    for arg in args:
        for ch in arg:
            if ch not in allowed_chars:
                raise RuntimeError('invalid segment %r' % arg)
    return os.path.join(*args)

def random_string(len=9):
    return os.urandom(len).encode('base64')[:len].replace('+', 'A').replace('/', 'B')
        
def _overwrite(path, content):
    new = path + '.tmp' + random_string()
    with open(new, 'w') as f:
        f.write(content)
    os.rename(new, path)

    

