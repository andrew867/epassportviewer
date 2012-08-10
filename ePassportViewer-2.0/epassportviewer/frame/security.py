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

from epassportviewer.const import *
from epassportviewer.dialog import Tooltip
from epassportviewer.util.configManager import configManager

class securityFrame(Frame):

    def __init__(self, master):
        Frame.__init__(self, master, relief=GROOVE, bd=1)
        
        
        self.BAC = Label(self, text="Basic Access Control", anchor=W)
        self.BAC.pack(side=TOP, expand=True, fill=BOTH)
        self.tipBAC = None
        
        self.AA = Label(self, text="Active Auth.", anchor=W)
        self.AA.pack(side=TOP, expand=True, fill=BOTH)
        self.tipAA = None
        
        
        self.PA = Label(self, text="Passive Auth.", anchor=W)
        self.PA.pack(side=LEFT, expand=True, fill=BOTH)
        self.tipPA = None
        
        dgFrame = Frame(self)
        dgFrame.pack(side=TOP, expand=True, fill=BOTH)
        self.dg = {}
        for dg in range(1,17):
            self.dg['DG'+str(dg)] = Label(self, text="DG"+str(dg))
            self.dg['DG'+str(dg)].pack(side=LEFT, expand=True, fill=BOTH)
        self.dg['SOD'] = Label(self, text=str('SOD'))
        self.dg['SOD'].pack(side=LEFT, expand=True, fill=BOTH)
        
    def setSecurity(self, BAC=None, AA=None, PA=None):
        green = "#00B738"
        orange = "#E28000"
        
        if BAC != None:
            if BAC == False:
                self.BAC.configure(fg='red')
            else: 
                self.BAC.configure(fg=green)
                self.tipBAC = Tooltip(parent=self.BAC, tip="The BAC succeed")
                        
        if AA != None:
            self.AA.configure(fg='black')
            if AA == True:
                self.AA.configure(fg=green)
                self.tipAA = Tooltip(parent=self.AA, tip="The AA succeed")
            elif AA == "NO_OPENSSL":
                self.AA.configure(fg=orange)
            elif AA == "NO_DG_15":
                self.AA.configure(fg=orange)
            elif AA == False:
                self.AA.configure(fg='red')
                    
        if PA != None:
            CA, PA = PA
            set = False
            for dg in PA:
                try:
                    self.dg[str(dg)].configure(fg='black')
                    if PA[dg] == True:
                        self.dg[str(dg)].configure(fg=green)
                    elif PA[dg] == False:
                        self.PA.configure(fg='red')
                        set = True
                        self.dg[str(dg)].configure(fg='red')
                    elif PA[dg] == "NO_OPENSSL":
                        self.dg[str(dg)].configure(fg=orange)
                except KeyError:
                    pass
                
            if CA == "NO_OPENSSL":
                self.PA.configure(fg=orange)
            elif not set:
                self.PA.configure(fg=green)
                self.tipPA = Tooltip(parent=self.PA, tip="The PA succeed")
            
            if CA != None:
                self.dg['SOD'].configure(fg='black')
                if CA == True:
                    self.dg['SOD'].configure(fg=green)
                elif CA == False:
                    self.dg['SOD'].configure(fg='red')
                elif CA == "NO_OPENSSL":
                    self.dg['SOD'].configure(fg=orange)
                    
        self.update()
                
    def clear(self):
        self.BAC.configure(fg='black')
        self.AA.configure(fg='black')
        self.PA.configure(fg='black')
        for dg in range(1,17):
            self.dg['DG'+str(dg)].configure(fg='black')
        self.dg['SOD'].configure(fg='black')
        
        if self.tipBAC:
            self.tipBAC.destroy()
            self.tipBAC = None
        if self.tipAA:
            self.tipAA.destroy()
            self.tipAA = None
        if self.tipPA:
            self.tipPA.destroy()
            self.tipPA = None
