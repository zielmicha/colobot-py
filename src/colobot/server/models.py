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

import threading
import os
import logging

from colobot.server.db import ProfileEntry, sha256, List, Dict, \
    join, File, NotFoundError, random_string

class Profile:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.make_dir()

        self.users = Users(self)
        self.sessions = Sessions(self)

    def make_dir(self, *args):
        path = os.path.join(self.path, join(*args))
        if not os.path.exists(path):
            os.makedirs(path)
        
    def get(self, *args, **kwargs):
        path = os.path.join(self.path, join(*args))
        return File(path, **kwargs)

class AuthenticationError(Exception):
    pass
    
class User:
    def __init__(self, profile, entry):
        self.entry = entry

    def check_permission(self, name):
        if self['login'] == 'root':
            return True
        return False # TODO: ACL

    def change_password(self, password, salt):
        self[salt] = salt
        self[password] = password
        self.profile.users.write()
    
    def __getitem__(self, name):
        return self.entry[name]

class Users(List):
    entry_cls = User
    
    def __init__(self, profile):
        self.file = profile.get('users')
        self.profile = profile
        try:
            self.get_by('login', 'root')
        except NotFoundError:
            self.create_root()

    def create_root(self):
        # create root with empty password
        self.create_user(login='root', mail='', password=sha256('\0'), salt='')

    def create_user(self, login, mail, password, salt):
        self.file.data.append({'login': login, 'mail': mail, 'password': password, 'salt': salt})
        self.file.write()

    def authenticate(self, auth_token, login, password_token):
        user = self.get_by('login', login)
        expected = sha256(auth_token + '\0' + user['password'])
        if expected == password_token:
            return self.get_by('login', login)
        else:
            logging.debug('authentication failed user: %r, token: %r, expected: %r, auth_token: %s', login, password_token, expected, auth_token)
            raise AuthenticationError()

class Sessions(List):
    def __init__(self, profile):
        self.profile = profile
        self.file = profile.get('sessions')

    def create_session(self, login):
        uid = random_string(12)
        self.file.data.append({'login': login, 'uid': uid})
        self.file.write()
        return uid

    def get_session(self, uid):
        return self.get_by('uid', uid)['login']
        
   
