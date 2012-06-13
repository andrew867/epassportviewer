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
from tkFileDialog import askdirectory, askopenfilename
import tkMessageBox

from epassportviewer.const import *
from epassportviewer.frame import mrzInput, overview, security, toolbar
from epassportviewer.util import configManager, callback, image, inOut, helper
from epassportviewer import dialog
from pypassport.doc9303 import converter
import pypassport

import time
import thread
import threading
import os

class Controller(Frame):
    
    def __init__(self, parent, confFile=CONFIG):
        self.parent = parent
        configManager.configManager().loadConfig(confFile)
        
        self.view = View(parent, self)
        
    def exit(self):
        self.parent.quit()
        
class View(Frame):
    
    PDF, XML, FACE, SIGN, FID, DG, CERTIFICATE, PKEY = xrange(8)
        
    def __init__(self, parent, controller):
        Frame.__init__(self, None) 
        
        self.parent = parent
        self.controller = controller
        self._doc = None

        self.mrz = StringVar()
        self.stop = BooleanVar()
        self.stop.set(False)
        
        self.pack()
        self.createLayout()
        self.bindEvents()

        self.parent.config(menu=self.getMenu())
        
        if configManager.configManager().getOption("Options", 'disclamer'):
            tkMessageBox.showwarning("Disclamer", DISCLAMER)
            configManager.configManager().setOption("Options", 'disclamer', False)
        
    def getMenu(self):            
        menu = Menu(self, relief=FLAT)
        
        # FILE
        fileMenu = Menu(menu, tearoff=0)        
        menu.add_cascade(label="File", underline=0, menu=fileMenu)
        fileMenu.add_command(label="Open", underline=0, command=self.load)
        
        fileMenu.add_cascade(label="Save", underline=0, command=self.save)
        fileMenu.add_cascade(label="Export", underline=0, command=self.export)
        fileMenu.add_command(label="Clear", underline=0, command=self.clear)
        fileMenu.add_separator()
        fileMenu.add_command(label="Quit", underline=0, command=self.exit)
        
        self.moreMenu = moreMenu = Menu(menu, tearoff=0, postcommand=self.refreshMore)
        menu.add_cascade(label="More", underline=0, menu=moreMenu)
        
        # CONFIGURE
        configureMenu = Menu(menu, tearoff=0)
        menu.add_cascade(label="Configure", underline=0, menu=configureMenu)     
        
#        self.readerMenu = Menu(menu, tearoff=0, postcommand=self.refreshReaders)
#        configureMenu.add_cascade(label="Reader", underline=0, menu=self.readerMenu)
#        
        self.securityMenu = Menu(menu, tearoff=0)
        self.securityMenu.add_checkbutton(label='Active Authentication', variable=configManager.configManager().getVariable('Security', 'aa'))
        self.securityMenu.add_checkbutton(label='Passive Authentication', variable=configManager.configManager().getVariable('Security','pa'))
        configureMenu.add_cascade(label="Security", underline=0, menu=self.securityMenu)
        
#        self.modeMenu = Menu(menu, tearoff=0)
#        self.modeMenu.add_radiobutton(label='SFI (Faster)', variable=configManager.configManager().getVariable('Options', 'mode'), value='SFI', state=DISABLED)
#        self.modeMenu.add_radiobutton(label='FS (Slower)', variable=configManager.configManager().getVariable('Options', 'mode'), value='FS', state=DISABLED)
#        configureMenu.add_cascade(label="Reading Mode", underline=0, menu=self.modeMenu)        
#        
        self.sslMenu = Menu(configureMenu, tearoff=0)
        self.sslMenu.add_command(label=configManager.configManager().getOption('Options','openssl'), command=None)
        self.sslMenu.add_separator()
        self.sslMenu.add_command(label="Change", 
                                  underline=0,
                                  command=callback.Callback(self.setOpenssl, 
                                                            configManager.configManager().getVariable('Options','openssl'),
                                                            self.sslMenu))  
        configureMenu.add_cascade(label="OpenSSL", underline=0, menu=self.sslMenu)
        
        self.pathMenu = Menu(configureMenu, tearoff=0)
        self.pathMenu.add_command(label=configManager.configManager().getOption('Options','path'), command=None)
        self.pathMenu.add_separator()
        self.pathMenu.add_command(label="Change", 
                                  underline=0,
                                  command=callback.Callback(self.setPath, 
                                                            configManager.configManager().getVariable('Options','path'),
                                                            self.pathMenu))  
        configureMenu.add_cascade(label="Export Path", underline=0, menu=self.pathMenu)
        
        self.certificateMenu = Menu(configureMenu, tearoff=0)
        self.certificateMenu.add_command(label=configManager.configManager().getOption('Options','certificate'), command=None)
        self.certificateMenu.add_separator()
        self.certificateMenu.add_command(label="Change",
                                         underline=0,
                                         command=callback.Callback(self.setPath, 
                                                                   configManager.configManager().getVariable('Options','certificate'),
                                                                   self.certificateMenu))
        self.certificateMenu.add_command(label="Import", underline=0, command=self.importCertificate)                
        configureMenu.add_cascade(label="Certificate Directory", underline=0, menu=self.certificateMenu)
        
        configureMenu.add_command(label="Reset to Default", underline=0, command=self.resetConfig)

        logMenu = Menu(menu, tearoff=0)
        logMenu.add_checkbutton(label="ePassport API", underline=0, variable=configManager.configManager().getVariable('Logs','api'))
        logMenu.add_checkbutton(label="Secure Messaging", underline=0, variable=configManager.configManager().getVariable('Logs','sm'))
        logMenu.add_checkbutton(label="APDU", underline=0, variable=configManager.configManager().getVariable('Logs','apdu'))
        logMenu.add_separator()
        logMenu.add_command(label="See Log file", underline=4, command=self.openLog)
        menu.add_cascade(label="Log", underline=0, menu=logMenu)
        
        helpMenu = Menu(menu, tearoff=0)
#        helpMenu.add_command(label="Help Contents", underline=0, command=None, state=DISABLED)
        helpMenu.add_command(label="Manual", underline=0, command=None, state=DISABLED)
        helpMenu.add_command(label="Website", underline=0, command=self.website, state=NORMAL)
        helpMenu.add_separator()
        helpMenu.add_command(label="About", underline=0, command=self.onAbout)
        menu.add_cascade(label="Help", underline=0, menu=helpMenu)        
        
        return menu
    
    def refreshMore(self):
        moreMenu = self.moreMenu
        moreMenu.delete(0,END)
        if self._doc: state=NORMAL
        else: state=DISABLED
        
        moreMenu.add_command(label="Additional data", underline=0, command=self.AdditionalData, state=state)
    
#    def refreshReaders(self):        
#        self.readerMenu.delete(0, END)
#        
#        try:
#            readers = pypassport.reader.ReaderManager().getReaderList()
#            for r in readers:
#                self.readerMenu.add_radiobutton(label=r, variable=configManager.configManager().getVariable('Options','reader'), value=r)
#        except NameError, msg:
#            pass
#        
#        self.readerMenu.add_radiobutton(label='Auto-Detect', underline=0, variable=configManager.configManager().getVariable('Options','reader'), value='Auto')   
        
    def setPath(self, variable, menu):
        directory = askdirectory(title="Select directory", mustexist=1)
        if directory:
            directory = str(directory)
            variable.set(directory)
            menu.entryconfigure(0, label=directory)
            if menu == self.certificateMenu:
                self.importCertificate()
                
    def setOpenssl(self, variable, menu):
        openssl = askopenfilename()
        if openssl:
            openssl = str(openssl)
            variable.set(openssl)
            menu.entryconfigure(0, label=openssl)

    def importCertificate(self):
        try:
            CA = pypassport.epassport.camanager.CAManager(configManager.configManager().getOption('Options','certificate'))
            CA.toHashes()
            tkMessageBox.showwarning("Import Certificate", 'All present certificates have been imported!') 
        except Exception, msg:
            if DEBUG: print "Error while importing certificates", msg
            else: tkMessageBox.showwarning("Error while importing certificates", msg)         
        
    def onAbout(self):
        dialog.About(self)
    
    def exit(self):
        configManager.configManager().saveConfig()
        self.controller.exit()

    def bindEvents(self):
        self.bind_all('<Control-O>', self.load)
        self.master.protocol("WM_DELETE_WINDOW", self.exit)
    
    def createLayout(self):
        self.input = mrzInput.mrzInputFrame(self, self.mrz, self.gotMRZ)
        self.input.pack(fill=BOTH, expand=True)
        self.overview = overview.Overview(self)
        self.overview.pack(fill=BOTH, expand=True, anchor=CENTER)
        self.security = security.securityFrame(self)
        self.security.pack(fill=BOTH, expand=True, anchor=CENTER)
        self.status = toolbar.StatusBar(self)
        self.status.pack(fill=BOTH, expand=True, anchor=CENTER)
        self.status.set("Version %s", "1.0")
        
    def log(self, name, data):
        
        l = []
        if configManager.configManager().getOption('Logs','api'): l.append("EPassport")
        if configManager.configManager().getOption('Logs','sm'): l.append("SM")
        if configManager.configManager().getOption('Logs','apdu'): l.append("ISO7816")
#        if configManager.configManager().getOption('Logs','bac'): l.append("BAC")
        
        if name in l:
            try:
                log = open(LOG, 'a')
                log.write(name + "> " + data+'\n')
            except Exception, msg:
                pass
            finally:
                log.close()
    
    def clearLog(self):
        if os.path.isfile(LOG):
            os.remove(LOG)
    
    def openLog(self, event=None):
        if os.path.isfile(LOG):
            dialog.Log(self, LOG)
        else:
            tkMessageBox.showinfo("No Log File", "There is no log file available")
    
    def gotMRZ(self, mrz, fingerprint=False):
        self.clear()
        self._doc = self._detectReader(mrz)
        if self._doc != None:
            self._doc.CSCADirectory = configManager.configManager().getOption('Options', 'certificate')
            self._doc.openSslDirectory = configManager.configManager().getOption('Options', 'openssl')
            self.clearLog()
            if fingerprint:
                self.Fingerprint(None)
            else:
                self._doc.register(self.log)
                self._readPassport(self._doc, fingerprint)            
            
    def load(self, event=None):
        directory = askdirectory(title="Select directory", mustexist=1)
        if directory:
            self.clear()
            directory = str(directory)
            r = pypassport.reader.ReaderManager().create("DumpReader")
            r.connect(directory)
            self._doc = pypassport.epassport.EPassport(r)
            self._doc.CSCADirectory = configManager.configManager().getOption('Options', 'certificate')
            self._doc.openSslDirectory = configManager.configManager().getOption('Options', 'openssl')
            try:
                self.t = dialog.ReadingDialog(self, self._doc, False)
                self.t.read.register(self._dgRead)
                self.t.showSafe()
            except pypassport.doc9303.bac.BACException, msg:
                tkMessageBox.showerror("Reader", "Please verify the MRZ:\n" + str(msg[0]))
            except Exception, msg:
                tkMessageBox.showerror("Reader", "Please verify data source:\n" + str(msg[0]))            
            
    def AdditionalData(self, event=None):
        if self._doc:
            dialog.AdditionalData(self, self._doc)
        else:
            tkMessageBox.showinfo("No document open", "Please open a document before.")
                
    def Fingerprint(self, event=None):
#        if self._doc:
        fp = pypassport.fingerPrint.FingerPrint(self._doc)
        dialog.FingerPrintDialog(self, fp.analyse())
#        else:
#            tkMessageBox.showinfo("No document open", "Please read a document before performing fingerprint")            
            
    def clear(self, event=None):
        self._doc = None
        self.input.clean()
        self.overview.clear()
        self.security.clear()
        self.status.clear()
        
    def _detectReader(self, mrz):
        
        tkMessageBox.showinfo("Reader", "Remove then drop the passport on a reader")
        reader = None
        
        try:
        
            reader = pypassport.reader.ReaderManager().waitForCard(3)
            return pypassport.epassport.EPassport(reader, mrz)
        
        except Exception, msg:
            tkMessageBox.showerror("ePassport not found", str(msg[0]))

            
    def _readPassport(self, doc, fingerprint=False):
        try:
            self.t = dialog.ReadingDialog(self, doc, fingerprint)
            self.t.read.register(self._dgRead)
    #            if fingerprint: self.t.register(self.log)
            self.t.show()
        except pypassport.doc9303.bac.BACException, msg:
            tkMessageBox.showerror("Reader", "Please verify the MRZ:\n" + str(msg[0]))
        except Exception, msg:
            tkMessageBox.showerror("Reader", "Please verify data source:\n" + str(msg[0]))
    
    def _dgRead(self, data):
        (DG, DGdata) = data
        if DG in ["61", "67", "6B", "6C", "75"]:
            self.overview.loadDG(DG, DGdata)
        if DG == '61':
            self.security.setSecurity(BAC=self._doc._iso7816._ciphering)
            name, mrz = self.extractOwnerInfo(DGdata)
            self.input.addToHistory(name, mrz)
        if DG == 'AA':
            self.security.setSecurity(AA=DGdata)
        if DG == 'PA':
            self.security.setSecurity(PA=DGdata)
    
    def extractOwnerInfo(self, data):
        if not data.has_key('5F1F') or not data.has_key('5F5B'): 
            raise Exception("Could not extract name/mrz")
        mrz = data['5F1F'][44:88]
        name = (data['5F5B']).split("<<")
        name = helper.getItem(name[0]) + " " + helper.getItem(name[1])
        return (name,mrz)
    
    PDF, XML, FACE, SIGN, FID, DG, CERTIFICATE, PKEY
    
    def save(self):
        """ Save the current doc9303 instance into format(s)
            
            @raise exception: "Nothing to save" if not doc9303 loaded
            @return: None 
        """
        if self._doc == None:
            tkMessageBox.showerror("Nothing to save", "Please open a document before saving")
            return
        
        dir = configManager.configManager().getOption('Options', 'path')
        if dir == '' or not os.path.isdir(dir):
            self.setPath(configManager.configManager().getVariable('Options', 'path'), self.pathMenu)
            dir = configManager.configManager().getOption('Options', 'path')
            
        self._doc.dump(dir)
        tkMessageBox.showinfo("Save successful", "Data have been saved in " + dir)
        
    def export(self):
        if self._doc == None:
            tkMessageBox.showerror("Nothing to save", "Please open a document before saving")
            return
        
        dir = configManager.configManager().getOption('Options', 'path')
        if dir == '' or not os.path.isdir(dir):
            self.setPath(configManager.configManager().getVariable('Options', 'path'), self.pathMenu)
            dir = configManager.configManager().getOption('Options', 'path')
        
        name, mrz = self.extractOwnerInfo(self._doc['DG1'])
        inOut.toPDF(self._doc, dir+os.path.sep+name+".pdf")            
        inOut.toXML(self._doc, dir+os.path.sep+name+".xml")
                
        tkMessageBox.showinfo("Export successful", "Data have been exported in " + dir)

    def website(self):
        import webbrowser
        webbrowser.open(WEBSITE)
        
    def resetConfig(self):
        configManager.configManager().defaultConfig(CONFIG)
        configManager.configManager().setOption("Options", 'disclamer', False)