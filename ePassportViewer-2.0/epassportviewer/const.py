# Copyright 2009 Jean-Francois Houzard, Olivier Roger
#
# This file is part of epassportviewer.
#
# epassportviewer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# epassportviewer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with epassportviewer.
# If not, see <http://www.gnu.org/licenses/>.

import os.path
import sys

# Options
DEBUG   = True
MAX_HISTORY = 10
TITLE   = 'ePassport Viewer'

if (sys.platform.startswith('linux')  or sys.platform == 'cygwin'):
    CONFIG  = os.path.expanduser('~/.ePV-config.ini')
    HISTORY = os.path.expanduser('~/.ePV-history')
    TMPDIR  = '/tmp'
else:
    CONFIG  = 'config.ini'
    HISTORY = 'history'
    TMPDIR  = '.'
LOG     = os.path.join(TMPDIR, 'ePV-system.log')
STDERR  = os.path.join(TMPDIR, 'ePV-error.log')
OUTFILE = os.path.join(TMPDIR, 'ePV-out.txt')

VERSION = '2.0'
WEBSITE = "http://code.google.com/p/epassportviewer/"
DISCLAMER = """Before using pyPassport, you must be sure that you are allowed to read the contactless\n chip of your passport, according to the laws and regulations of the country that issued it."""
LICENSE = "LICENSE"
CONTACT = "antonin.beaujeant@uclouvain.be"

