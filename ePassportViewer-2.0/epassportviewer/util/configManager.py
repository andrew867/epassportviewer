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

# usefull information about configparser module
# src: http://effbot.org/librarybook/configparser.htm

import ConfigParser
from Tkinter import *

from epassportviewer.const import *
from epassportviewer.util import singleton

class configManager(singleton.Singleton, dict):
    
    default = {'Options':{'reader'      : 'Auto',
                          'driver'      : '',
                          'path'        : '',
                          'certificate' : '',
                          'openssl'     : 'openssl',
                          'disclamer'   : True
                          },
               'Security':{'aa'         : True,
                           'pa'         : True
                          },
                'Logs':   {'api'        : True,
                           'sm'         : False,
                           'apdu'       : False
                           }
            }

    def initialize(self):
        self['Options'] = {}
        self['Options']['reader'] = StringVar()
        self['Options']['driver'] = StringVar()
        self['Options']['path'] = StringVar()
        self['Options']['certificate'] = StringVar()
        self['Options']['openssl'] = StringVar()
        self['Options']['disclamer'] = BooleanVar()
        
        self['Security'] = {}
        self['Security']['aa'] = BooleanVar()
        self['Security']['pa'] = BooleanVar()
        
        self['Logs'] = {}
        self['Logs']['api'] = BooleanVar()
        self['Logs']['sm'] = BooleanVar()
        self['Logs']['apdu'] = BooleanVar()

    def loadConfig(self, file=CONFIG, autoSaveChanges=True):            
        self.parser = ConfigParser.ConfigParser()
        self.parser.read(file)
        parser = self.parser
        self.file = file
        self.autoSaveChanges = autoSaveChanges
        
        self.defaultConfig(self.default)
        for section in parser.sections():
            for option in parser.options(section):
                try:
                    self[section][option].set(parser.get(section,option))
                    if autoSaveChanges:
                        self[section][option].trace('w', self.saveConfig)
                # Don't import unspecified settings
                except KeyError, msg:
                    pass
        self.refresh()
                    
    def defaultConfig(self, config):
        for section in self.default:
            for option in self.default[section]:
                self[section][option].set(self.default[section][option])
    
    def saveConfig(self, *args):
        parser = self.parser
        
        for section in self:
            if not parser.has_section(section):
                parser.add_section(section)
            for option in self[section]:
                parser.set(section, option, self[section][option].get())
        
        file = open(self.file, 'w')
        parser.write(file)
        file.close()
        
    # Required to set boolean fields correclty.. don't know why
    def refresh(self):
        for section in self:
            for option in self[section]:
                self[section][option].set(self[section][option].get())
                
    def getVariable(self, section, option):            
        return self[section][option]
    
    def getOption(self, section, option):
        return self[section][option].get()
    
    def setOption(self, section, option, value):
        self[section][option].set(value)
        return True