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
import tkMessageBox
import pickle

from epassportviewer.const import *
from epassportviewer.util import callback

from pypassport import epassport

class mrzInputFrame(Frame):
        
    def __init__(self, master, mrz, callback):
        Frame.__init__(self, master, relief=GROOVE, bd=1)
        
        self.mrz = mrz
        self.callback = callback
        
        self.createLayout()
        self.bindEvents()
        
    def createLayout(self):
        row = 0
        Label(self, text="MRZ").pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        self.mrzEntry = Entry(self, width=48, textvariable=self.mrz)
        self.mrzEntry.pack(side=LEFT, fill=X, expand=True, padx=2, pady=2)
        self.mrzEntry.focus_set()
        
        self.readButton = Button(self, text="Viewer", command=self.read, state=NORMAL)
        self.readButton.pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        
        self.attacksButton = Button(self, text="Attacks", command=None, state=NORMAL)
        self.attacksButton.pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        
        self.customButton = Button(self, text="Custom", command=None, state=NORMAL)
        self.customButton.pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        
        #self.fingerprintButton = Button(self, text="Fingerprint", command=self.fingerprint, state=NORMAL)
        #self.fingerprintButton.pack(side=LEFT, fill=BOTH, padx=2, pady=2)        
        
        #self.historyButton = Menubutton(self, text="History", relief=RAISED)
        #self.historyButton.pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        #self.historyButton.menu = Menu(self.historyButton, tearoff=0, postcommand=self.refreshHistory)
        #self.historyButton.config(menu=self.historyButton.menu)
        
        self.update()
    
    def bindEvents(self):
        self.mrzEntry.bind("<Return>", self.process)
        
    def clean(self):
#       self.mrz.set("")
        self.setColor('white')
        
    def setMRZ(self, mrz):
        self.mrz.set(mrz)
        
    def setColor(self, color):
        self.mrzEntry['bg'] = color
        self.update()
        self.mrzEntry.focus_set()
        
    def checkMRZ(self):
        data = self.correctMRZ(self.mrz.get())
        mrz = epassport.mrz.MRZ(data)
        mrz.checkMRZ()
        self.setColor('green')
        return data

    # Correct Reading errors for OCR Pen (tested with IRIS PEN EXPRESS 6)
    def correctMRZ(self, mrz):
        mrz = mrz.strip()
        if len(mrz) > 10 and mrz[9] == "O":
            mrz = mrz[:9] + "0" + mrz[10:]
            self.mrzEntry.delete(0, END)
            self.mrzEntry.insert(0, mrz)
        return mrz
    
    def read(self, event=None):
        self.process()
        
    def fingerprint(self, event=None):
        mrz = self.mrz.get()
        self.correctMRZ(mrz)
        mrz = self.checkMRZ()
        self.callback(mrz, True)
    
    def process(self):
        try:
            mrz = self.mrz.get()
            self.correctMRZ(mrz)
            mrz = self.checkMRZ()
            self.callback(mrz)
        except epassport.mrz.MRZException, msg:
            if DEBUG: print msg
            else: tkMessageBox.showerror("Read Error", msg) 
            self.setColor('red')     
    
    # History Functions      
    def loadHistory(self, filename=HISTORY):
        try: 
            file = open(filename, "r")
            history = pickle.load(file)
            file.close()
            return history
        except Exception, msg:
            return []
    
    def saveHistory(self, history, filename=HISTORY):
        try:
            file = open(filename, "w")
            pickle.dump(history, file)
            file.close()
        except Exception,msg:
            pass
        
    def addToHistory(self, name, mrz):
        history = self.loadHistory()
        if (name,mrz) in history: 
            history.remove((name,mrz))
        history.insert(0,(name,mrz))
        if len(history) > MAX_HISTORY:
            history = history[:MAX_HISTORY]
        self.saveHistory(history)
        
    def refreshHistory(self, event=None):
        self.historyButton.menu.delete(0, END)
        for name, mrz in self.loadHistory():
            self.historyButton.menu.add_command(label=name, command=callback.Callback(self.setMRZ, mrz))
