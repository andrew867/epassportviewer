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

from Tkinter import *
from epassportviewer.const import *

class Toolbar(Frame):
    def __init__(self, master, relief=FLAT, bd=2):
        Frame.__init__(self, master, relief=relief, bd=bd)
        self._buttons = {}

    def addButton(self, id, text, command=None, state=DISABLED, side=LEFT, fill=BOTH, expand=True, anchor=E):
        self._buttons[id] = Button(self, text=text, command=command, state=state)
        self._buttons[id].pack(padx=2, pady=2, anchor=anchor, side=side, fill=fill, expand=expand)

    def set(self, id, key, value):
        self._buttons[id][key] = value

class StatusBar(Frame):
   def __init__(self, master):
      Frame.__init__(self, master)
      self.label = Label(self, bd=1, relief=SUNKEN, anchor=W)
      self.label.pack(fill=X)

   def set(self, format, *args):
      self.label.config(text=format % args, anchor=E)
      self.label.update_idletasks()

   def clear(self):
      self.label.config(text="Version {0}".format(VERSION))
      self.label.update_idletasks()
