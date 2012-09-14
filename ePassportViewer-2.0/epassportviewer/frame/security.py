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

from pypassport.doc9303.converter import *

from epassportviewer.const import *
from epassportviewer.dialog import Tooltip
from epassportviewer.util.configManager import configManager

class securityFrame(Frame):

    def __init__(self, master):
        Frame.__init__(self, master)
        
        bacFrame = Frame(self)
        bacFrame.pack(side=TOP, expand=True, fill=BOTH)
        self.BAC = Label(bacFrame, text="Basic Access Control")
        self.BAC.pack(side=LEFT)
        self.tipBAC = None
        
        aaFrame = Frame(self)
        aaFrame.pack(side=TOP, expand=True, fill=BOTH)
        self.AA = Label(aaFrame, text="Active Auth.")
        self.AA.pack(side=LEFT)
        self.tipAA = None
        
        paFrame = Frame(self)
        paFrame.pack(side=TOP, expand=True, fill=BOTH)
        self.PA = Label(paFrame, text="Passive Auth.")
        self.PA.pack(side=LEFT)
        self.tipPA = None
        
        dgFrame = Frame(paFrame)
        dgFrame.pack(side=LEFT, expand=True, fill=BOTH)
        self.dg = {}
        self.tips = {}
        for dg in range(1,17):
            self.tips['DG'+str(dg)] = None
            self.dg['DG'+str(dg)] = Label(dgFrame, text="DG"+str(dg))
            self.dg['DG'+str(dg)].pack(side=LEFT, expand=True, fill=BOTH)
        self.dg['SOD'] = Label(dgFrame, text=str('SOD'))
        self.dg['SOD'].pack(side=LEFT, expand=True, fill=BOTH)
        self.tips['SOD'] = None
        
    def setSecurity(self, BAC=None, AA=None, PA=None, EAC=None):
        green = "#00B738"
        orange = "#E28000"
        hashfail = False
        
        # Basic Access Control label
        if BAC != None:
            if BAC == False:
                self.BAC.configure(fg='red')
                self.tipBAC = Tooltip(parent=self.BAC, tip="The BAC failed. Check you wrote the correct MRZ.")
            else: 
                self.BAC.configure(fg=green)
                self.tipBAC = Tooltip(parent=self.BAC, tip="The BAC succeed")
        
        # Active Authentication label
        if AA != None:
            self.AA.configure(fg='black')
            if AA == True:
                self.AA.configure(fg=green)
                self.tipAA = Tooltip(parent=self.AA, tip="The active authentication succeed")
            elif AA == "NO_OPENSSL":
                self.AA.configure(fg=orange)
                self.tipAA = Tooltip(parent=self.AA, tip="Cannot use OpenSSL.")
            elif AA == "NO_DG_15":
                self.tipAA = Tooltip(parent=self.AA, tip="There is no private key (DG15).\nNot possible to execute an active authentication.")
                self.AA.configure(fg=orange)
            elif AA == False:
                self.AA.configure(fg='red')
                    
        if PA != None:
            CA, PA = PA
            set = False
            
            # DGs labels
            for dg in range(1,17):
                if not self.tips['DG'+str(dg)]:
                    self.tips['DG'+str(dg)] = Tooltip(parent=self.dg['DG'+str(dg)], tip="DG not present.")
            for dg in PA:
                try:
                    self.dg[str(dg)].configure(fg='black')
                    if PA[dg] == True:
                        self.dg[str(dg)].configure(fg=green)
                        self.tips[str(dg)].destroy()
                        self.tips[str(dg)] = Tooltip(parent=self.dg[str(dg)], tip="Intergrity verified with the SOD")
                    elif PA[dg] == False:
                        hashfail = True
                        self.PA.configure(fg='red')
                        set = True
                        self.dg[str(dg)].configure(fg='red')
                        self.tips[str(dg)].destroy()
                        self.tips[str(dg)] = Tooltip(parent=self.dg[str(dg)], tip="Hashes does not match (with SOD)")
                    elif PA[dg] == "NO_OPENSSL":
                        self.dg[str(dg)].configure(fg=orange)
                        self.tips[str(dg)].destroy()
                        self.tips[str(dg)] = Tooltip(parent=self.dg[str(dg)], tip="Cannot use OpenSSL.")
                except KeyError:
                    pass
            
            # Passive Authentication label
            if not hashfail:
                if CA == "OPENSSL_ERROR":
                    self.PA.configure(fg=orange)
                    self.tipsPA = Tooltip(parent=self.PA, tip="SOD not verify with CSCA.\nCheck you load the correct certificate")
                elif CA == "CA_NOT_SET":
                    self.PA.configure(fg=orange)
                    self.tipPA = Tooltip(parent=self.PA, tip='No CSCA certificate loaded. Cannot verify the SOD.\nPlease go to "Configure > Import root certificate..."')
                elif CA == True:
                    self.PA.configure(fg=green)
                    self.tipPA = Tooltip(parent=self.PA, tip="The PA succeed")
                else:
                    self.PA.configure(fg='red')
                    self.tipPA = Tooltip(parent=self.PA, tip="SOD not verify with CSCA")
            else:
                self.PA.configure(fg='red')
                self.tipPA = Tooltip(parent=self.PA, tip="One or more hash does not match with the SOD")
                
            if CA == "OPENSSL_ERROR":
                self.dg['SOD'].configure(fg=orange)
                self.tips['SOD'] = Tooltip(parent=self.dg['SOD'], tip="SOD not verify with CSCA.\nCheck you load the correct certificate")
            elif CA == "CA_NOT_SET":
                self.dg['SOD'].configure(fg=orange)
                self.tips['SOD'] = Tooltip(parent=self.dg['SOD'], tip='No CSCA certificate loaded. Cannot verify the SOD.\nPlease go to "Configure > Import root certificate..."')
            elif CA == True:
                self.dg['SOD'].configure(fg=green)
                self.tips['SOD'] = Tooltip(parent=self.dg['SOD'], tip="Intergrity verified with the CSCA")
            else:
                self.dg['SOD'].configure(fg='red')
                self.tips['SOD'] = Tooltip(parent=self.dg['SOD'], tip="SOD not verify with CSCA")
                
                    
        if EAC != None:
            self.dg[toDG(EAC)].configure(fg='red')
            self.tips[toDG(EAC)] = Tooltip(parent=self.dg[toDG(EAC)], tip="EAC is not yet implemented.\nThus it is not possible to read this DG.")
        
        self.update()
                
    def clear(self):
        self.BAC.configure(fg='black')
        self.AA.configure(fg='black')
        self.PA.configure(fg='black')
        for dg in range(1,17):
            self.dg['DG'+str(dg)].configure(fg='black')
            if self.tips['DG'+str(dg)]:
                self.tips['DG'+str(dg)].destroy()
                self.tips['DG'+str(dg)] = None
            self.tips['DG'+str(dg)] = None
        self.dg['SOD'].configure(fg='black')
        if self.tips['SOD']:
                self.tips['SOD'].destroy()
                self.tips['SOD'] = None
        
        if self.tipBAC:
            self.tipBAC.destroy()
            self.tipBAC = None
        if self.tipAA:
            self.tipAA.destroy()
            self.tipAA = None
        if self.tipPA:
            self.tipPA.destroy()
            self.tipPA = None
