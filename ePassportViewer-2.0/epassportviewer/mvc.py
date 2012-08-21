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
try:
    import gtk
    GTK = True
except:
    GTK = False
import re
from Tkinter import *
from tkFileDialog import askdirectory, askopenfilename
import tkMessageBox

from epassportviewer.const import *
from epassportviewer.frame import mrzInput, overview, security, toolbar, attacks, custom
from epassportviewer.util import configManager, callback, image, inOut, helper
from epassportviewer import dialog
from pypassport.doc9303 import converter
from pypassport import epassport
import pypassport

import time
import thread
import threading
import os
import pickle


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
        self.t = None

        self.passportNo = StringVar()
        self.dob = StringVar()
        self.doe = StringVar()
        self.stop = BooleanVar()
        self.stop.set(False)
        
        self.pack()
        
        ## MRZ ##
        self.mrzFrame = Frame(self, relief=RAISED, bd=1)
        self.mrzFrame.pack(fill=BOTH, expand=True)
        self.createMRZ()
        
        ## VIEWER ##        
        self.viewerFrame = Frame(self, relief=RAISED, borderwidth=1)
        self.overview = overview.Overview(self.viewerFrame, self)
        self.overview.pack(fill=BOTH, expand=True, anchor=CENTER)
        self.footer = toolbar.StatusBar(self.viewerFrame)
        self.footer.pack(fill=BOTH, expand=True, anchor=CENTER)
        self.footer.set("Version %s", VERSION)
        
        self.currentFrame = self.viewerFrame
        self.currentFrame.pack(fill=BOTH, expand=1)
        
        ## ATTACKS ##
        self.attacksFrame = Frame(self, borderwidth=1)
        self.attacksFrameTest = attacks.AttacksFrame(self.attacksFrame, self)
        self.attacksFrameTest.pack(fill=BOTH, expand=1)
        
        ## CUSTOM ##
        self.customFrame = Frame(self, borderwidth=1)
        self.customFrameTest = custom.CustomFrame(self.customFrame, self)
        self.customFrameTest.pack(fill=BOTH, expand=1)

        self.bindEvents()

        self.parent.config(menu=self.getMenu())
        
        if configManager.configManager().getOption("Options", 'disclamer'):
            tkMessageBox.showwarning("Disclamer", DISCLAMER)
            configManager.configManager().setOption("Options", 'disclamer', False)
    
    #def createViewer(self):
    #    overviewMenuFrame = Frame(self.viewerFrame, borderwidth=1, relief=GROOVE)
    #    overviewMenuFrame.pack(fill=BOTH, expand=1)
    #    
    #    self.overview = overview.Overview(self.viewerFrame, self)
    #    self.overview.pack(fill=BOTH, expand=True, anchor=CENTER)

    #    self.footer = toolbar.StatusBar(self.viewerFrame)
    #    self.footer.pack(fill=BOTH, expand=True, anchor=CENTER)
    #    self.footer.set("Version %s", VERSION)
    
    def createMRZ(self):
        
        Label(self.mrzFrame, text="Passport no").pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        
        self.numberEntry = Entry(self.mrzFrame, width=9, textvariable=self.passportNo)
        self.numberEntry.pack(side=LEFT, fill=X, expand=True, padx=2, pady=2)
        
        Label(self.mrzFrame, text="Date of birth").pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        
        self.dobEntry = Entry(self.mrzFrame, width=7, textvariable=self.dob)
        self.dobEntry.pack(side=LEFT, fill=X, expand=True, padx=2, pady=2)
        self.dob.set("YYMMDD")
        
        Label(self.mrzFrame, text="Date of expiracy").pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        
        self.doeEntry = Entry(self.mrzFrame, width=7, textvariable=self.doe)
        self.doeEntry.pack(side=LEFT, fill=X, expand=True, padx=2, pady=2)
        self.doe.set("YYMMDD")
        
        self.readButton = Button(self.mrzFrame, text="Viewer", command=self.viewerSwitch)
        self.readButton.pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        
        self.attacksButton = Button(self.mrzFrame, text="Attacks", command=self.attacksSwitch)
        self.attacksButton.pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        
        self.customButton = Button(self.mrzFrame, text="Custom", command=self.customSwitch)
        self.customButton.pack(side=LEFT, fill=BOTH, padx=2, pady=2)
        
        self.currentB = self.readButton
        self.currentB.config(relief=SUNKEN)
        
    
    def bindEvents(self):
        self.bind_all('<Control-O>', self.load)
        self.master.protocol("WM_DELETE_WINDOW", self.exit)
        
    def getMenu(self):  
                  
        menu = Menu(self, relief=FLAT)
        
        ####################
        #       FILE       #
        ####################
        fileMenu = Menu(menu, tearoff=0)
        fileMenu.add_command(label="Create...", underline=0, command=self.create)
        fileMenu.add_separator()    
        fileMenu.add_command(label="Open...", underline=0, command=self.load)
        fileMenu.add_command(label="Save...", underline=0, command=self.save)
        saveAs = Menu(fileMenu, tearoff=0)
        saveAs.add_command(label="Generate", underline=0, command=self.fingerprint)
        saveAs.add_command(label="PDF...", underline=0, command=self.exportToPDF)
        saveAs.add_command(label="XML...", underline=0, command=self.exportToXML)                
        fileMenu.add_cascade(label="Generate report", underline=0, menu=saveAs)
        fileMenu.add_command(label="Clear", underline=0, command=self.clearFull)
        fileMenu.add_separator()
        fileMenu.add_command(label="Quit", underline=0, command=self.exit)
        menu.add_cascade(label="File", underline=0, menu=fileMenu)
        
        
        ####################
        #      HISTORY     #
        ####################
        self.historyMenu = Menu(menu, tearoff=0, postcommand=self.refreshHistory)        
        menu.add_cascade(label="History", underline=0, menu=self.historyMenu)
        

        ####################
        #     CONFIGURE    #
        ####################
        configureMenu = Menu(menu, tearoff=0, postcommand=self.refreshReaders)

        self.readerMenu = Menu(menu, tearoff=0)
        configureMenu.add_cascade(label="Readers", underline=0, menu=self.readerMenu)
        
        self.securityMenu = Menu(menu, tearoff=0)
        self.securityMenu.add_checkbutton(  label='Active Authentication', 
                                            variable=configManager.configManager().getVariable('Security', 'aa'))
        self.securityMenu.add_checkbutton(  label='Passive Authentication', 
                                            variable=configManager.configManager().getVariable('Security','pa'))
        
        
        configureMenu.add_cascade(label="Security", underline=0, menu=self.securityMenu)
        
        #self.sslMenu = Menu(configureMenu, tearoff=0)
        #self.sslMenu.add_command(label=configManager.configManager().getOption('Options','openssl'), command=None)
        #self.sslMenu.add_separator()
        #self.sslMenu.add_command(label="Change", 
        #                          underline=0,
        #                          command=callback.Callback(self.setOpenssl, 
        #                                                    configManager.configManager().getVariable('Options','openssl'),
        #                                                    self.sslMenu))  
        #configureMenu.add_cascade(label="OpenSSL", underline=0, menu=self.sslMenu)
        
        #self.certificateMenu = Menu(configureMenu, tearoff=0)
        #self.certificateMenu.add_command(label=configManager.configManager().getOption('Options','certificate'), command=None)
        #self.certificateMenu.add_separator()
        #self.certificateMenu.add_command(label="Change",
        #                                 underline=0,
        #                                 command=callback.Callback(self.setPath, 
        #                                                           configManager.configManager().getVariable('Options','certificate'),
        #                                                           self.certificateMenu))
        #self.certificateMenu.add_command(label="Import", underline=0, command=self.importCertificate)                
        #configureMenu.add_cascade(label="Certificate Directory", underline=0, menu=self.certificateMenu)
        
        configureMenu.add_command(label="Import root certificates...", underline=0, command=self.importCertificate)
        configureMenu.add_separator()
        configureMenu.add_command(label="Reset to default", underline=0, command=self.resetConfig)
        
        menu.add_cascade(label="Configure", underline=0, menu=configureMenu)

        
        ####################
        #     LOG MENU     #
        ####################
        
        #logMenu = Menu(menu, tearoff=0)
        #logMenu.add_checkbutton(label="ePassport API", underline=0, variable=configManager.configManager().getVariable('Logs','api'))
        #logMenu.add_checkbutton(label="Secure Messaging", underline=0, variable=configManager.configManager().getVariable('Logs','sm'))
        #logMenu.add_checkbutton(label="APDU", underline=0, variable=configManager.configManager().getVariable('Logs','apdu'))
        #logMenu.add_separator()
        #logMenu.add_command(label="See Log file", underline=4, command=self.openLog)
        #menu.add_cascade(label="Log", underline=0, menu=logMenu)
        
        
        ###################
        #    HELP MENU    #
        ###################
        
        helpMenu = Menu(menu, tearoff=0)
        if os.name == "nt" or os.name == "posix":
            manualState = NORMAL
        else:
            manualState = DISABLED
        helpMenu.add_command(label="Manual", underline=0, command=self.openManual, state=manualState)
        
        helpMenu.add_command(label="Website", underline=0, command=self.website)
        helpMenu.add_separator()
        helpMenu.add_command(label="About", underline=0, command=self.onAbout)
        menu.add_cascade(label="Help", underline=0, menu=helpMenu)        
        
        return menu
    
    
    def refreshReaders(self):        
        self.readerMenu.delete(0, END)
        
        try:
            readers = pypassport.reader.ReaderManager().getReaderList()
            i = 0
            for r in readers:
                self.readerMenu.add_radiobutton(label=r, variable=configManager.configManager().getVariable('Options','reader'), value=i, state=DISABLED)
                i += 1
        except NameError, msg:
            pass
        
        self.readerMenu.add_radiobutton(label='Auto-Detect', underline=0, variable=configManager.configManager().getVariable('Options','reader'), value='Auto')   
        
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
        directory = askdirectory(title="Select directory", mustexist=1)
        if directory:
            directory = str(directory)
            try:
                CA = pypassport.camanager.CAManager(directory)
                CA.toHashes()
                tkMessageBox.showwarning("Import Certificate", 'All present certificates have been imported!') 
            except Exception, msg:
                if DEBUG: print "Error while importing certificates", msg
                else: tkMessageBox.showwarning("Error while importing certificates", msg)         
        
    def onAbout(self):
        dialog.About(self)

    def attacksSwitch(self):
        self.currentB.config(relief=RAISED)
        self.currentB = self.attacksButton
        self.currentB.config(relief=SUNKEN)
        
        self.currentFrame.pack_forget()
        self.currentFrame = self.attacksFrame
        self.currentFrame.pack(fill=BOTH, expand=1)
    
    def viewerSwitch(self, event=None):
        self.currentB.config(relief=RAISED)
        self.currentB = self.readButton
        self.currentB.config(relief=SUNKEN)
        
        self.currentFrame.pack_forget()
        self.currentFrame = self.viewerFrame
        self.currentFrame.pack(fill=BOTH, expand=1)
    
    def customSwitch(self, event=None):
        self.currentB.config(relief=RAISED)
        self.currentB = self.customButton
        self.currentB.config(relief=SUNKEN)
        
        self.currentFrame.pack_forget()
        self.currentFrame = self.customFrame
        self.currentFrame.pack(fill=BOTH, expand=1)
    
    def exit(self):
        configManager.configManager().saveConfig()
        self.controller.exit()
        
    def log(self, name, data):
        
        l = ["EPassport", "SM", "ISO7816", "BAC"]
        
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
            dialog.Log(self)
        else:
            tkMessageBox.showinfo("No Log File", "There is no log file available")
    
    def clearFull(self):
        self.clean()
        self.clearMRZ()
        os.remove(LOG)
        
        
    def clean(self):
        self.overview.clear()
        self.overview.security.clear()
        self.footer.clear()
        self.setColorNo('white')
        self.setColorDob('white')
        self.setColorDoe('white')
        self.clear()
    
    def clear(self):
        self._doc = None
        self.t = None
        
    def clearMRZ(self):
        self.passportNo.set("")
        self.dob.set("YYMMDD")
        self.doe.set("YYMMDD")
    
    #############
    # CALLBACKS #
    #############
    def gotMRZ(self, mrz, fingerprint=False):
            
        self._doc = self._detectReader(mrz)
        
        if self._doc != None:
            self._doc.CSCADirectory = configManager.configManager().getOption('Options', 'certificate')
            self._doc.openSslDirectory = configManager.configManager().getOption('Options', 'openssl')
            self.clearLog()
            if fingerprint:
                self.Fingerprint()
            else:
                self._doc.register(self.log)
                self._readPassport()
                self.overview.additionalButton.config(state=NORMAL)
                self.overview.logButton.config(state=NORMAL)
       
    def load(self, event=None):
        directory = askdirectory(title="Select directory", mustexist=1)
        if directory:
            self.clean()
            directory = str(directory)
            r = pypassport.reader.ReaderManager().create("DumpReader")
            r.connect(directory)
            self._doc = pypassport.epassport.EPassport(r)
            self._doc.CSCADirectory = configManager.configManager().getOption('Options', 'certificate')
            self._doc.openSslDirectory = configManager.configManager().getOption('Options', 'openssl')
            try:
                self.t = dialog.ReadingDialog(self, self._doc)
                self.t.read.register(self._dgRead)
                self.t.showSafe()
            except pypassport.doc9303.bac.BACException, msg:
                tkMessageBox.showerror("Reader", "Please verify the MRZ:\n" + str(msg[0]))
            except Exception, msg:
                tkMessageBox.showerror("Reader", "Please verify data source:\n" + str(msg[0]))            
            
    def AdditionalData(self):
        try:
            if GTK:
                tvexample = dialog.AdditionalDialog(self.t.ep)
                gtk.main()
            else:
                dialog.AdditionalData(self, self.t.ep)
        except Exception, msg:
            tkMessageBox.showinfo("No document open", "Please open a document before.\n{0}".format(str(msg)))
    
    
    def create(self, event=None):
        try:
            dialog.create(self)
        except Exception, msg:
            tkMessageBox.showinfo("Error create", msg)
    
    
    def Fingerprint(self):
        try:
            self.thFp = dialog.FingerprintProcess(self, self._doc)
            self.thFp.showSafe()
        except Exception, msg:
            tkMessageBox.showinfo("No document open", msg)
        
    def _detectReader(self, mrz):
        reader = None
        
        try:
            reader = pypassport.reader.ReaderManager().waitForCard()
            return pypassport.epassport.EPassport(reader, mrz)
        except Exception, msg:
            tkMessageBox.showerror("ePassport not found", "{0}.\nPlease check you passport is on the reader".format(str(msg)))

            
    def _readPassport(self):
        try:
            self.t = dialog.ReadingDialog(self, self._doc)
            self.t.read.register(self._dgRead)
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
            name, mrz = self.extractOwnerInfo(DGdata)
            self.addToHistory(name, mrz)
        if DG == 'BAC':
            self.overview.security.setSecurity(BAC=DGdata)
        if DG == 'AA':
            self.overview.security.setSecurity(AA=DGdata)
        if DG == 'PA':
            self.overview.security.setSecurity(PA=DGdata)
        if DG == 'EAC':
            self.overview.security.setSecurity(EAC=DGdata)
    
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
            tkMessageBox.showinfo("Nothing to save", "Please open a document before saving")
            return
        
        directory = askdirectory(title="Select directory", mustexist=1)
        if directory:
            directory = str(directory)
            self._doc.dump(directory)
            tkMessageBox.showinfo("Save successful", "Data have been saved in " + directory)
        
    
    def exportToXML(self):
        if self.t == None:
            tkMessageBox.showinfo("Nothing to save", "Please open a document before saving")
            return
        
        directory = askdirectory(title="Select directory", mustexist=1)
        if directory:
            directory = str(directory)
            name, mrz = self.extractOwnerInfo(self._doc['DG1'])
            inOut.toXML(self.t.ep, directory+os.path.sep+name+".xml")           
            tkMessageBox.showinfo("Export successful", "Data have been exported in " + directory)
        
    
    def exportToPDF(self):
        if self.t == None:
            tkMessageBox.showinfo("Nothing to save", "Please open a document before saving")
            return
        
        directory = askdirectory(title="Select directory", mustexist=1)
        if directory:
            directory = str(directory)
            name, mrz = self.extractOwnerInfo(self._doc['DG1'])
            inOut.toPDF(self.t.ep, directory+os.path.sep+name+".pdf")            
            tkMessageBox.showinfo("Export successful", "Data have been exported in " + directory)


    def website(self):
        import webbrowser
        webbrowser.open(WEBSITE)
    
    def openManual(self):
        if os.name == "nt":
            os.filestart("manual.pdf")
        elif os.name == "posix":
            os.system("/usr/bin/xdg-open manual.pdf")  
            
    def resetConfig(self):
        configManager.configManager().defaultConfig(CONFIG)
        configManager.configManager().setOption("Options", 'disclamer', False)
    
    
    ################################
    # METHODS FROM FORMER MRZINPUT #
    ################################

        
    def setMRZ(self, mrz):
        passportNo = mrz[0:9]
        passportNo = passportNo.replace("<", "")
        dob = mrz[13:19]
        doe = mrz[21:27]

        self.passportNo.set(passportNo)
        self.dob.set(dob)
        self.doe.set(doe)
    
    def setColor(self, color):
        self.numberEntry['bg'] = color
        self.dobEntry['bg'] = color
        self.doeEntry['bg'] = color
        self.update()
        self.numberEntry.focus_set()
        
    def setColorNo(self, color):
        self.numberEntry['bg'] = color
        self.update()
        self.numberEntry.focus_set()
        
    def setColorDob(self, color):
        self.dobEntry['bg'] = color
        self.update()
        self.numberEntry.focus_set()
    
    def setColorDoe(self, color):
        self.doeEntry['bg'] = color
        self.update()
        self.numberEntry.focus_set()
        
    def checkMRZ(self):
        self.passportNo.set(self.passportNo.get().upper())
        
        check = True
        
        pattern_id = '^[0-9A-Z<]{8,9}$'
        pattern_date = "^\d\d(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])$"
        
        reg=re.compile(pattern_id)
        if not reg.match(self.passportNo.get()):
            self.setColorNo("red")
            check = False
        
        reg=re.compile(pattern_date)
        if not reg.match(self.dob.get()):
            self.setColorDob("red")
            check = False
        
        reg=re.compile(pattern_date)
        if not reg.match(self.doe.get()):
            self.setColorDoe("red")
            check = False
            
        return check
        
    def _calculCheckDigit(self, value):
        """ From pypassport > doc9303 > mrz"""
        weighting = [7,3,1]
        weight = {'0':0, '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '<':0,
          'A':10, 'B':11, 'C':12, 'D':13, 'E':14, 'F':15, 'G':16, 'H':17, 'I':18, 'J':19, 'K':20, 'L':21, 'M':22, 
          'N':23, 'O':24, 'P':25, 'Q':26, 'R':27, 'S':28, 'T':29, 'U':30, 'V':31, 'W':32, 'X':33, 'Y':34, 'Z':35};
        cpt=0
        res=0
        for x in value:
            tmp = weight[str(x)] * weighting[cpt%3]
            res += tmp
            cpt += 1
        return str(res%10)
    
    def buildMRZ(self):
        """From pypassport > attacks > bruteForce"""
        
        id_pass = self.passportNo.get()
        dob = self.dob.get()
        exp = self.doe.get()
        pers_num="<<<<<<<<<<<<<<"
        if id_pass=="" or dob=="" or pers_num=="": return None
        id_pass_full = id_pass + (9-len(id_pass))*'<' + self._calculCheckDigit(id_pass)
        dob_full = dob + self._calculCheckDigit(dob)
        exp_full = exp + self._calculCheckDigit(exp)
        pers_num_full = pers_num + self._calculCheckDigit(pers_num)
        return id_pass_full + "???" + dob_full + "?" + exp_full + pers_num_full + self._calculCheckDigit(id_pass_full+dob_full+exp_full+pers_num_full)
        
    def fingerprint(self):
        try:
            self.clear()
            if self.checkMRZ():
                mrz = self.buildMRZ()
                self.gotMRZ(mrz, True)
        except epassport.mrz.MRZException, msg:
            if DEBUG: print msg
            else: tkMessageBox.showerror("Read Error", msg) 
            self.setColor('red')
    
    def process(self):
        try:
            self.clean()
            if self.checkMRZ():
                mrz = self.buildMRZ()
                self.gotMRZ(mrz)
            
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
        with open(filename, 'w') as file:
            pickle.dump(history, file)
            file.close()
        
    def addToHistory(self, name, mrz):
        history = self.loadHistory()
        for name_hist, mrz_hist in history:
            if mrz==mrz_hist: history.remove((name_hist, mrz_hist))
        history.insert(0,(name,mrz))
        if len(history) > MAX_HISTORY:
            history = history[:MAX_HISTORY]
        self.saveHistory(history)
        
    def refreshHistory(self):
        self.historyMenu.delete(0, END)
        i = 0
        for name, mrz in self.loadHistory():
            i += 1
            self.historyMenu.add_command(label=name, command=callback.Callback(self.setMRZ, mrz))
        if i: clearstate=NORMAL
        else: 
            self.historyMenu.add_command(label="Empty", underline=0, state=DISABLED)
            clearstate=DISABLED
        self.historyMenu.add_separator()
        self.historyMenu.add_command(label="Clear", underline=0, state=clearstate, command=self.clearHistory)
        
    def clearHistory(self):
        os.remove(HISTORY)
        
        
