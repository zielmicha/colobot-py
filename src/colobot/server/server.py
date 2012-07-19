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
import threading
import functools
import time
import logging

import colobot.server.db
import colobot.game

from colobot.server.models import Profile
from colobot.server.db import random_string

class Server:
    def __init__(self, profile, loader):
        self.profile = profile
        self.loader = loader
        self.lock = threading.RLock()
        self.games = {}

    def _init(self, address):
        thread = multisock.SocketThread()
        acceptor = thread.listen(address)
        acceptor.accept.bind(self.accept)
        return thread
        
    def run(self, address):
        self._init(address).loop()

    def start(self, address):
        self._init(address).start()

    def accept(self, socket):
        ConnectionHandler(server=self, profile=self.profile, socket=socket)

    # -----------------------------

    def create_game(self, name):
        if name in self.games:
            raise KeyError(name)

        self.games[name] = colobot.game.Game(self.loader)

class ConnectionHandler:
    def __init__(self, server, profile, socket):
        self.server = server
        self.socket = socket
        self.profile = profile
        self.user = None
        
        self.reset_auth_token()
        self.setup_connection()

    def reset_auth_token(self):
        self.auth_token = random_string(20)
        
    def setup_connection(self):
        main = self.socket.get_main_channel()
        self.rpc = multisock.jsonrpc.JsonRpcChannel(main, async=True)
        self.rpc.server = self

    def rpc__getAttributeNames(self):
        # for iPython
        return [ name[4:] for name in dir(self) if name.startswith('rpc_') ]

    def rpc_trait_names(self):
        # for iPython
        return []

    # --------------------------
        
    def rpc_get_auth_tokens(self, login):
        return {'token': self.auth_token,
                'salt': self.profile.users.get_by('login', login)['salt'] if login else None}

    def rpc_authenticate(self, login, password_token):
        self.user = self.profile.users.authenticate(self.auth_token, login, password_token)
        self.reset_auth_token()
        return self.profile.sessions.create_session(self.user['login'])

    def rpc_use_session(self, uid):
        name = self.profile.sessions.get_session(uid)
        self.user = self.profile.users.get_by('login', name)
    
    def rpc_passwd(self, login, password_token, salt):
        if login != self.user.login:
            self.user.check_permission('manage-users')
        self.profile.users.get_by('name', login).change_password(password=password_token, salt=salt)

    def rpc_list_games(self):
        return self.server.games.keys()

    def rpc_create_game(self, name):
        self.user.check_permission('create-games')
        self.server.create_game(name)

    def rpc_load_terrain(self, game_name, name):
        self.server.games[game_name].load_terrain(name)
