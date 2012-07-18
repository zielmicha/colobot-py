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

def setup_path():
    import sys, os
    path = os.environ.get('MULTISOCK_PATH')
    if not path:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'multisock')

    if not os.path.exists(os.path.join(path, 'multisock')):
        print >>sys.stderr, 'Looks like you haven\'t cloned submodules. Execute:'
        print >>sys.stderr, '\tgit submodule init'
        print >>sys.stderr, '\tgit submodule update'
        print >>sys.stderr
        
    sys.path.append(path)
