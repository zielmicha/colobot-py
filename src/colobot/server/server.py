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
import os
import json

import colobot.server.db
import colobot.game

from colobot.server.models import Profile
from colobot.server.db import random_string

import g3d.serialize

SHA1_LENGTH = 20 # TODO: move to colobot.common

class Server:
    def __init__(self, profile, loader):
        self.profile = profile
        self.loader = loader
        self.serializer = g3d.serialize.Serializer()
        self.lock = threading.RLock()
        self.game_ticker = g3d.Timer(min_interval=0.05)
        self.games = {}

        multisock.async(lambda: (multisock.set_thread_name('games'),
                                 self.game_ticker.loop()))

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

        game = self.games[name] = colobot.game.Game(self.loader)
        self.game_ticker.add_ticker(game.tick)

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

    def rpc_eval(self, code):
        if self.user['login'] != 'root':
            raise RuntimeError('only root can eval')
        if os.environ['COLOBOT_EVAL'] != 'allow':
            raise RuntimeError('COLOBOT_EVAL env varible not set to "allow"')

        return eval(code, {'server': self.server, 'user': self.user, 'self': self})

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

    def rpc_get_dependencies(self, objects_sha1):
        l = []
        for object_sha1 in objects_sha1:
            l += self.server.serializer.get_dependencies_by_sha1(object_sha1.decode('hex'))
        return [ ident.encode('hex') for ident in l ]

    def rpc_get_resources(self, identifiers):
        channel = self.socket.new_channel()
        for ident in identifiers:
            ident = ident.decode('hex')
            assert type(ident) == str and len(ident) == SHA1_LENGTH, repr(ident)
            data = self.server.serializer.get_by_sha1(ident)
            channel.send_async(ident + data)
        return channel.id

    # ---- GAME -----

    def rpc_load_terrain(self, game_name, name):
        self.user.check_game_permission(game_name, 'manage')
        self.server.games[game_name].load_terrain(name)

    def rpc_get_terrain(self, game_name):
        terrain = self.server.games[game_name].terrain
        return self.server.serializer.add(terrain).encode('hex')

    def rpc_open_update_channel(self, game_name):
        channel = self.socket.new_channel()
        handler = UpdateChannelHandler(channel, self.server, self.server.games[game_name])
        multisock.async(handler.loop)
        return channel.id

    def rpc_create_static_object(self, game_name, model_name):
        self.user.check_game_permission(game_name, 'manage')
        self.server.games[game_name].create_static_object(self.user.login, model_name)

    def rpc_get_user_objects(self, game_name):
        return [ object.ident for object in
                 self.server.games[game_name].get_player_objects(self.user.login) ]

    def rpc_motor(self, game_name, bot_id, motor):
        self.server.games[game_name].motor(self.user.login, bot_id, motor)

    def rpc_load_scene(self, game_name, scene_name):
        self.user.check_game_permission(game_name, 'manage')
        self.server.games[game_name].load_scene(scene_name)


class UpdateChannelHandler(object):
    def __init__(self, channel, server, game):
        self.channel = channel
        self.game = game
        self.server = server

        self.last_objects = set()

    def loop(self):
        multisock.set_thread_name('update sender')
        timer = g3d.Timer(min_interval=0.1)
        timer.add_ticker(self.tick)
        timer.loop()

    def tick(self, _):
        # TODO: use denser format
        objects = set(self.game.get_objects())

        new_objects = objects - self.last_objects
        deleted_objects = self.last_objects - objects
        updates = []

        updates_time = time.time()
        for obj in objects:
            updates.append((obj.ident, obj.position, obj.velocity, obj.rotation, None))

        data = (
                updates_time,
                [ (obj.ident, self.server.serializer.add(obj.model)) for obj in new_objects ],
                [ obj.ident for obj in deleted_objects ],
                updates,
        )

        blob = self.server.serializer.serialize(data)
        self.channel.send(blob)

        self.last_objects = objects
