# Copyright 2013 Louis Demay
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

try:
    # Try first if pypassport is installed on the system
    import pypassport
except:
    # Otherwise use the local version
    import sys
    import os.path
    sys.path.append(os.path.join('..', 'pypassport-2.0'))
    import pypassport

from epassportviewer.util import configManager

def getReaderList():
	return pypassport.reader.ReaderManager().getReaderList()

def waitForCard():
    reader = None
    my_reader = configManager.configManager().getOption('Options','reader')
    my_driver = configManager.configManager().getOption('Options','driver')
    if my_reader != "Auto":
        reader = pypassport.reader.ReaderManager().waitForCard(5, my_driver, my_reader)
    else:
        reader = pypassport.reader.ReaderManager().waitForCard()
    return reader
