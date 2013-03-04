#!/usr/bin/python2.7

# Copyright 2012 Jean-Francois Houzard, Olivier Roger, Antonin Beaujeant
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
Error = False
import traceback,sys
import os
import tkMessageBox
from Tkinter import *
try:
    import Image, ImageTk
    from epassportviewer.const import *
    from epassportviewer.mvc import Controller
    from epassportviewer.util.image import ImageFactory
except Exception, msg:
    print msg
    tkMessageBox.showerror("PCSC Error", msg)
    Error = True

class dummyStream(object):
    ''' dummyStream behaves like a stream but does nothing. '''
    def __init__(self):
        self.f = open(OUTFILE, 'w')
    def write(self,data):
        self.f.write(data)
    def read(self,data): pass
    def flush(self):
        self.f.flush()
    def close(self):
        self.f.close()

sys.stdout = dummyStream()
sys.stderr = dummyStream()
sys.stdin = dummyStream()
sys.__stdout__ = dummyStream()
sys.__stderr__ = dummyStream()
sys.__stdin__ = dummyStream()

def run():

    root = Tk()
    root.resizable(width = False, height = False)
    #TODO: Linux get error, windows not (missing app.ico)
    try:
        root.iconbitmap(os.path.join(os.path.dirname(os.path.realpath(__file__)), "app.ico"))
    except Exception, msg:
        pass
    # remove console on osx from http://mail.python.org/pipermail/python-list/2006-October/578318.html
    if (sys.platform != "win32") and hasattr(sys, 'frozen'):
        root.tk.call('console', 'hide')
    app = Controller(parent=root)
    root.title(TITLE)
    root.mainloop()

if __name__ == "__main__":
    if not Error:
        run()
