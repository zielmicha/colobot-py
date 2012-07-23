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

import colobot.server.models
import colobot.server.server
import colobot.loader

import argparse
import logging
import glob

DEFAULT_PATH = '~/.colobot'
DEFAULT_ADDRESS = 'tcp:localhost:2718'

parser = argparse.ArgumentParser(description='Start Colobot-py server.')
parser.add_argument('--profile', metavar='PROFILE', dest='profile',
                    default=DEFAULT_PATH,
                   help='where to store server data (default: %(default)s)')
parser.add_argument('--address', metavar='ADDRESS', dest='address',
                   default=DEFAULT_ADDRESS, # notice that default port == int(e*1000)
                   help='address to bind (in form tcp:host:port or anything multisock accepts)'
                    ' (default: %(default)s)')
parser.add_argument('--log', metavar='LEVEL', dest='logging',
                    default='INFO', choices=['INFO', 'DEBUG', 'ERROR'],
                    help='logging level, one of: DEBUG, INFO, ERROR')

args = parser.parse_args()

logging.basicConfig(level=getattr(logging, args.logging.upper()))

profile = colobot.server.models.Profile(os.path.expanduser(args.profile))
loader = colobot.loader.Loader()

for path in glob.glob('data/*'):
    if os.path.isdir(path):
        loader.add_directory(path)

colobot.server.server.Server(profile=profile, loader=loader).run(args.address)
