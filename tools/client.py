#!/usr/bin/python
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

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import colobot
colobot.setup_path()

import colobot.client
import colobot.client.ui
import getpass
import logging

logging.basicConfig(level=logging.DEBUG)

client = colobot.client.Client(sys.argv[1])
if not client.authenticate_with_session():
    login = raw_input('Username: ')
    password = getpass.getpass()
    client.authenticate_and_save(login, password)

def open_window(name):
    global win
    win = colobot.client.ui.UIWindow(client, name)
    win.setup()
    win.loop()

client.create_game('game')
client.load_scene('game', 'scene103.txt')
#client.load_terrain('game', 'relief15.png')
#client.rpc.call.create_static_object('game', 'wheeled-transporter.model')
#client.rpc.call.create_static_object('game', 'wheeled-transporter.model')

open_window('game')

from IPython import embed
embed()
