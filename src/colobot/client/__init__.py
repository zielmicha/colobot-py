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
import time
import logging
import StringIO

import g3d.serialize

# make sure that serializer knows all used modules
import g3d.model
import colobot.game

CACHE_PATH = os.path.expanduser('~/.cache/colobot')

def sha256(x):
    return hashlib.sha256(x).hexdigest()

SHA1_LENGTH = 20

def rpc_wrapper(name):
    ' Returns function that calls self.rpc.`name` '
    def func(self, *args, **kwargs):
        return self.rpc.call_func(name, *args, **kwargs)
    func.__name__ = name
    return func

class Client:
    def __init__(self, address):
        self.unserializer = g3d.serialize.Unserializer()
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
    motor = rpc_wrapper('motor')
    load_scene = rpc_wrapper('load_scene')

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

    def fetch_objects(self, idents):
        idents = list(set( ident for ident in idents
                      if ident not in self.unserializer.cache ))
        if not idents:
            return
        logging.debug('fetching %s', [ id.encode('hex') for id in idents ])
        deps = list(set(self.get_dependencies(idents) + idents))
        for sha1, data in self.get_resources(deps):
            assert sha1 in deps, '%r not in %s' % (sha1, deps)
            logging.debug('adding %s', sha1.encode('hex'))
            self.unserializer.add(sha1, data)
        logging.debug('done')

    def get_terrain(self, game_name):
        ident = self.rpc.call.get_terrain(game_name).decode('hex')
        self.fetch_objects([ident])
        return self.unserializer.load(ident)

    def get_resources(self, idents):
        channel_id = self.rpc.call.get_resources([ i.encode('hex') for i in idents ])
        channel = self.socket.get_channel(channel_id)

        for i in xrange(len(idents)):
            packet = channel.recv()
            yield packet[ :SHA1_LENGTH], packet[SHA1_LENGTH: ]

    def get_dependencies(self, idents):
        return [ i.decode('hex')
                 for i in self.rpc.call.get_dependencies([ i.encode('hex')
                                                           for i in idents ]) ]

    def open_update_channel(self, name):
        return self.socket.get_channel(self.rpc.call.open_update_channel(name))


class UpdateReader:
    def __init__(self, client, channel):
        self.channel = channel
        self.client = client

        self.unserialized = multisock.Operation()
        multisock.async(self.loop)

    def loop(self):
        multisock.set_thread_name('update recv')
        try:
            while True:
                self.tick()
        finally:
            self.unserialized.close()

    def tick(self):
        blob = self.channel.recv()
        data = self.client.unserializer.load_from(StringIO.StringIO(blob))

        update_time, new, deleted, updates = data

        self.client.fetch_objects([ model for ident, model in new ])

        val = (
                time, # TODO: synchronize time with server
                [ (ident, self.client.unserializer.load(model)) for ident, model in new ],
                deleted,
                updates
        )

        if self.unserialized._queue.qsize() > 3:
            # FIXME: use of private varibles
            # TODO: use UDP and avoid this
            # skip update if client is not fast enough
            return
        self.unserialized.dispatch(val)


    def get_new_updates(self):
        ''' Retruns None if new updates haven\'t arrived yet. Never blocks. '''
        try:
            return self.unserialized.noblock()
        except multisock.Operation.WouldBlock:
            return None
