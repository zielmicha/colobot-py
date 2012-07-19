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

import multisock
import multisock.jsonrpc

import hashlib
import os

import logging

CACHE_PATH = os.path.expanduser('~/.cache/colobot')

def sha256(x):
    return hashlib.sha256(x).hexdigest()

def rpc_wrapper(name):
    ' Returns function that calls self.rpc.`name` '
    def func(self, *args, **kwargs):
        return self.rpc.call_func(name, *args, **kwargs)
    func.__name__ = name
    return func

class Client:
    def __init__(self, address):
        self.socket = multisock.connect(address)
        self.rpc = multisock.jsonrpc.JsonRpcChannel(self.socket.get_main_channel())

    def authenticate(self, login, password):
        auth_data = self.rpc.call.get_auth_tokens(login)
        auth_token, salt = auth_data['token'], auth_data['salt']
        password_token = sha256(auth_token + '\0' + sha256(password + '\0' + salt))
        return self.rpc.call.authenticate(login, password_token)

    use_session = rpc_wrapper('use_session')
    create_game = rpc_wrapper('create_game')
    list_games = rpc_wrapper('list_games')
    load_terrain = rpc_wrapper('load_terrain')

    def authenticate_with_session(self):
        ''' Tries to login with saved session.
        If it returns False you need to manually authenticate with
        authenticate_and_save'''
        session = self.load_session()
        
        if session:
            try:
                self.use_session(session)
                logging.info('Successfuly authenticated with session')
                return True
            except multisock.jsonrpc.RemoteError as exc:
                logging.info('Authentication with session failed: %s', exc)
                return False
        else:
            logging.info('Session file not found')
            return False

    def authenticate_and_save(self, login, password):
        session = self.authenticate(login, password)
        self.save_session(session)

    def load_session(self):
        path = os.path.join(CACHE_PATH, 'session')
        try:
            return open(path).read()
        except IOError:
            return None

    def save_session(self, uid):
        if not os.path.exists(CACHE_PATH):
            os.makedirs(CACHE_PATH)
        path = os.path.join(CACHE_PATH, 'session')
        with open(path, 'w') as f:
            f.write(uid)

