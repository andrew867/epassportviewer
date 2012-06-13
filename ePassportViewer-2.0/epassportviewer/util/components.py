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

#TODO: Make generic widget like in http://code.activestate.com/recipes/52266/

from Tkinter import *
class MulticolumnList():
    def __init__(self, master, data, columnHeaders=[], height=10, onSelect=None, bindings=[]):
        
        self._master = master
        self._data = data
        self._height = height
        self._callback = onSelect
        
        self.pane=Frame(master);
        self.scroll = Scrollbar (self.pane, orient=VERTICAL )
        self.scroll.pack (fill=BOTH, anchor=E, expand=False, side=RIGHT)
        self.pane.pack(expand=True, fill=BOTH, side=TOP, anchor=W)
        self.scroll["command"] = self.move_to
        
        self.columns = []
        for i in range(self._findMaxLength(self._data)):
            container = Frame(self.pane)
            try:
                Label(container, text=columnHeaders[i]).pack(side=TOP)
            except:
                pass
            column = Listbox(container, 
                             height=self._height,
                             width=1, 
                             yscrollcommand=self.scroll.set,
                             selectmode=SINGLE,
                             selectbackground='skyblue',
                             activestyle='none', #'dotbox',
                             bd=0)
            column.pack(expand=True, fill=BOTH, side=LEFT, anchor=N+W)
            container.pack(expand=True, fill=BOTH, side=LEFT, anchor=N+W)
            self.columns.append(column)
        
        self.refresh()
        self.bindEvents(bindings)
    
    def bindEvents(self, bindings):
        for column in self.columns:
            column.bind("<ButtonRelease-1>", self.onSelectionChanged)
            column.bind("<Double-1>", self.onSelect)
            column.bind("<Return>", self.onSelect)
            column.bind("<FocusIn>", self.onFocus)
            column.bind("<<ListboxSelect>>", self.onSelectionChanged)
            column.bind("<KeyPress-Up>", self.onUp)
            column.bind("<KeyPress-Down>", self.onDown)
            
            # Linux
            column.bind('<Button-4>', self.onMouseWheel)
            column.bind('<Button-5>', self.onMouseWheel)
            # Windows
            column.bind('<MouseWheel>', self.onMouseWheel)
            
            if bindings:
                for event, callback in bindings:
                    column.bind(event, callback) 
    
    def setData(self, data):
        self.clear()
        self._data = data
        self.refresh()
    
    def _findMaxLength(self, data):
        result = 0
        for i in data:
            if type(i) == []:
                raise Exception("Item must be lists")
            if len(i) > result:
                result = len(i)
        return result
        
    def _loadData(self):
        if self._data != None:
            for item in self._data:
                for i in range(len(item)):
                    self.columns[i].insert(END, item[i])
                    if self.columns[i]['width'] < len(item[i]):
                        self.columns[i]['width'] = len(item[i])        
    
    def refresh(self):
        self._loadData()
        
    def onSelectionChanged(self, event):
        try:
            index, = event.widget.curselection()
        except ValueError: #No selected item
            index = 0
        index = int(index)
        event.widget.focus_set()
        event.widget.activate(index)
        self.colorSelection(index)
        
    def colorSelection(self, index):
        for column in self.columns:
            for i in range(column.size()):
                if i == int(index):
                    column.activate(i)
                    column.see(i)
                    column.itemconfig(i, bg="skyblue", fg='white')
                else:
                    column.itemconfig(i, bg="white", fg='black')
                    
    def onMouseWheel(self, event):
        # respond to Linux or Windows wheel event
        orient = None
        if event.num == 5 or event.delta == -120:
#            self.onDown(event)
            orient = 1
        if event.num == 4 or event.delta == 120:
#            self.onUp(event)
            orient = -1
        if orient:
            for column in self.columns:
                column.yview(SCROLL, orient, UNITS)
                
    def onUp(self, event=None):
        try:
            index, = event.widget.curselection()
        except ValueError: #No selected item
            return
        index = int(index)
        if index > 0:
            event.widget.selection_clear(0,END)
            event.widget.selection_set(index-1)
            self.colorSelection(index-1)
        
    def onDown(self, event=None):
        try:
            index, = event.widget.curselection()
        except ValueError: #No selected item
            return
        index = int(index)
        if index < event.widget.size()-1:
            event.widget.selection_clear(0,END)
            event.widget.selection_set(index+1)
            self.colorSelection(index+1)                 
            
    def onSelect(self, event):
        try:
            index, = event.widget.curselection()
        except ValueError: #No selected item
            return
        if self._callback:
            self._callback(self._data[int(index)])
#        else :
#            print 'Selected', self._data[int(index)]
            
    def onFocus(self, event):
        self.onSelectionChanged(event)

    def move_to(self, cmd, event, units=None):
        for column in self.columns:
            column.yview_moveto(event)
            
    def clear(self):
        self._data = None
        for i in range(len(self.columns)):
            self.columns[i].delete(0, END)
#            self.columns[i]['width'] = 0 # Too many resize -> ugly
        self.refresh()
        
    def focus_set(self):
        if self.columns[0]:
            self.columns[0].focus_set()
            self.columns[0].selection_set(0)

class DataGroupGridList(MulticolumnList):
    def __init__(self, master, data, columnHeaders=[], height=4, onSelect=None, bindings=[]):
        MulticolumnList.__init__(self, master, data, columnHeaders, height, onSelect, bindings)
    
    def _findMaxLength(self, data):
        return 2
        
    def _loadData(self):
        def insert(column, item):
            self.columns[column].insert(END, item)
            if self.columns[column]['width'] < len(item):
                self.columns[column]['width'] = len(item) + 5
                
        if self._data != None:                 
            for dg in self._data:
                insert(0, dg)
                insert(1, self._data[dg])
                
    def load(self, data):
        self.clear()
        self._data = data
        self._loadData()