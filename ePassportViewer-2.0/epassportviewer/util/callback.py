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

# Src : http://www.daniweb.com/forums/thread38770.html

class Callback:
    """handles arguments for callback functions"""
    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        return apply(self.callback, self.args, self.kwargs)

# USAGE
#
#from Tkinter import *
#
#def call(what=None):
#    print "call =", what
#    if what == 'red':
#        b1.config(bg="#ff0000")
#    if what == 'blue':
#        b2.config(bg="#0000ff")
#
#root = Tk()
#
## create the menubar
#menubar = Menu(root)
#
#filemenu = Menu(menubar)
#filemenu.add_command(label="Open", command=Callback(call, "open"))
#filemenu.add_command(label="Save", command=Callback(call, "save"))
#filemenu.add_command(label="Save as", command=Callback(call, "saveas"))
#filemenu.add_separator()
#filemenu.add_command(label="Quit", command=root.destroy) # better than root.quit (at least in IDLE)
#
#menubar.add_cascade(label="File", menu=filemenu)
#
#root.config(menu=menubar)
#
## create a toolbar with two buttons
## use Frame(root, borderwidth=2, relief='raised') for more separation
#toolbar = Frame(root)
#
#b1 = Button(toolbar, text="red", width=6, command=Callback(call, "red"))
#b1.pack(side=LEFT, padx=2, pady=2)
#b2 = Button(toolbar, text="blue", width=6, command=Callback(call, "blue"))
#b2.pack(side=LEFT, padx=2, pady=2)
#
#toolbar.pack(side=TOP, fill=X)
#
#mainloop()