# Copyright 2012 Antonin Beaujeant
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
import thread
import threading
import Image, ImageTk
import Queue
import time
from tkFileDialog import askdirectory, askopenfilename

from epassportviewer.const import *
from epassportviewer.util.image import ImageFactory
from epassportviewer.util.components import DataGroupGridList
from epassportviewer.util.configManager import configManager

##### NEW #####
from attacks import macTraceability
from pypassport import reader
from pypassport.iso7816 import Iso7816
from pypassport.doc9303.mrz import MRZ
###############

from pypassport import epassport
from pypassport import fingerPrint
from pypassport.doc9303 import datagroup
from pypassport.doc9303.converter import *

###################
#     ATTACKS     #
###################


##################
# MAC TRACEABILITY
##################

class MacTraceabilityWindow(Toplevel):

    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.title("MAC Traceability")
        self.resizable(False, False)
        
        im = Image.open(ImageFactory().create(ImageFactory().HELP))
        image = ImageTk.PhotoImage(im)
        
        # CONFIG
        configFrame = Frame(self, relief=RAISED, borderwidth=1)
        configFrame.pack(fill=BOTH, expand=1)
        
        nbLabel = Label(configFrame, text="Reader #:", justify=LEFT)
        nbLabel.pack(side=LEFT, padx=5, pady=5)
        
        self.nbForm = Entry(configFrame, width=2)
        self.nbForm.pack(side=LEFT)
        
        self.frenchVar = IntVar()
        frenchCheck = Checkbutton(configFrame, text="French passport", variable=self.frenchVar)
        frenchCheck.pack(side=LEFT, padx=20, pady=5)
        
        helpconfig = Button(configFrame, image=image, command=self.helpConfigDialog)
        helpconfig.image = image
        helpconfig.pack(side=RIGHT, padx=5, pady=5)
        
        # MRZ
        mrzFrame = Frame(self, relief=RAISED, borderwidth=1)
        mrzFrame.pack(fill=BOTH, expand=1)
        
        mrzLabel = Label(mrzFrame, text="MRZ", justify=LEFT)
        mrzLabel.pack(side=LEFT, padx=5, pady=5)
        
        self.mrzForm = Entry(mrzFrame, width=48)
        self.mrzForm.pack(side=LEFT, padx=5, pady=5)
        
        # IS VULNERABLE?
        vulnFrame = Frame(self, relief=RAISED, borderwidth=1)
        vulnFrame.pack(fill=BOTH, expand=1)
        
        vulnerableButton = Button(vulnFrame, text="Is vulnerable?", command=self.isVulnerable)
        vulnerableButton.pack(side=LEFT, padx=5, pady=5)
        
        coLabel = Label(vulnFrame, text="Cut-off:", justify=LEFT)
        coLabel.pack(side=LEFT, padx=5, pady=5)
        
        self.coForm = Entry(vulnFrame, width=3)
        self.coForm.pack(side=LEFT, padx=5, pady=5)
        
        helpVuln = Button(vulnFrame, image=image, command=self.helpVulnDialog)
        helpVuln.image = image
        helpVuln.pack(side=RIGHT, padx=5, pady=5)
        
        # SAVE PAIR
        saveFrame = Frame(self, relief=RAISED, borderwidth=1)
        saveFrame.pack(fill=BOTH, expand=1)
        
        saveButton = Button(saveFrame, text="Save pair...", command=self.save)
        saveButton.pack(side=LEFT, padx=5, pady=5)
        
        helpSave = Button(saveFrame, image=image, command=self.helpSaveDialog)
        helpSave.image = image
        helpSave.pack(side=RIGHT, padx=5, pady=5)
        
        # CHECK FROM FILE
        checkFrame = Frame(self, relief=RAISED, borderwidth=1)
        checkFrame.pack(fill=BOTH, expand=1)
        
        checkButton = Button(checkFrame, text="Check from file...", command=self.checkFromFile)
        checkButton.pack(side=LEFT, padx=5, pady=5)
        
        coFileLabel = Label(checkFrame, text="Cut-off:", justify=LEFT)
        coFileLabel.pack(side=LEFT, padx=5, pady=5)
        
        self.coFileForm = Entry(checkFrame, width=3)
        self.coFileForm.pack(side=LEFT, padx=5, pady=5)
        
        helpCheck = Button(checkFrame, image=image, command=self.helpCheckDialog)
        helpCheck.image = image
        helpCheck.pack(side=RIGHT, padx=5, pady=5)
        
        # TEST
        testFrame = Frame(self, relief=RAISED, borderwidth=1)
        testFrame.pack(fill=BOTH, expand=1)
        
        testButton = Button(testFrame, text="Perfom test", command=self.test)
        testButton.pack(side=LEFT, padx=5, pady=5)
        
        untilLabel = Label(testFrame, text="Until:", justify=LEFT)
        untilLabel.pack(side=LEFT, padx=5, pady=5)

        self.untilForm = Entry(testFrame, width=2)
        self.untilForm.pack(side=LEFT, padx=5, pady=5)
        
        delayLabel = Label(testFrame, text="Accuracy:", justify=LEFT)
        delayLabel.pack(side=LEFT, padx=5, pady=5)
        
        self.perDelayForm = Entry(testFrame, width=2)
        self.perDelayForm.pack(side=LEFT, padx=5, pady=5)
        
        helpTest = Button(testFrame, image=image, command=self.helpTestDialog)
        helpTest.image = image
        helpTest.pack(side=RIGHT, padx=5, pady=5)
        
        # RESET BAC
        rstFrame = Frame(self, relief=RAISED, borderwidth=1)
        rstFrame.pack(fill=BOTH, expand=1)
        
        rstButton = Button(rstFrame, text="Reset BAC", command=self.reset)
        rstButton.pack(side=LEFT, padx=5, pady=5)
        
        helpRst = Button(rstFrame, image=image, command=self.helpRstDialog)
        helpRst.image = image
        helpRst.pack(side=RIGHT, padx=5, pady=5)
        
        # DEMO
        demoFrame = Frame(self, relief=RAISED, borderwidth=1)
        demoFrame.pack(fill=BOTH, expand=1)
        
        demoButton = Button(demoFrame, text="Demo", command=self.demo)
        demoButton.pack(side=LEFT, padx=5, pady=5)
        
        helpDemo = Button(demoFrame, image=image, command=self.helpDemoDialog)
        helpDemo.image = image
        helpDemo.pack(side=RIGHT, padx=5, pady=5)
        
        # LOG
        logFrame = Frame(self, relief=RAISED, borderwidth=1)
        logFrame.pack(fill=BOTH, expand=1)
        
        self.log = Text(logFrame, height=15, width=62, state='disabled', wrap='none')
        self.log.grid()
        
        # VERBOSE
        verboseFrame = Frame(self, relief=RAISED, borderwidth=1)
        verboseFrame.pack(fill=BOTH, expand=1)

        self.verboseVar = IntVar()
        verboseCheck = Checkbutton(verboseFrame, text="Verbose", variable=self.verboseVar)
        verboseCheck.pack(side=LEFT, padx=5, pady=5)
    
    #########
    # METHODS
    #########
    
    def writeToLog(self, msg):
        self.log['state'] = 'normal'
        self.log.insert('1.0', "{0}\n".format(msg))
        self.log['state'] = 'disabled'
    
    
    ########
    # ACTION
    ########
    
    # IS VULNERABLE?
    def isVulnerable(self):
        try:

            if self.nbForm.get(): nb = self.nbForm.get()
            else: nb = 0
            
            if self.coForm.get(): co = self.coForm.get()
            else: co = 1.7

            r = reader.ReaderManager().waitForCard(5, "PcscReader", int(nb))
            attack = macTraceability.MacTraceability(Iso7816(r))
            if attack.setMRZ(self.mrzForm.get()):
                if self.frenchVar.get(): attack.reachMaxDelay()
                self.writeToLog("Is vulnerable? : {0}".format(attack.isVulnerable(int(co))))
            else:
                tkMessageBox.showerror("Error: Wrong MRZ", "The check digits are not correct")

        except Exception, msg:
            tkMessageBox.showerror("Error: is vulnerable", str(msg))
    
    # SAVE
    def save(self):
        
        try:
            
            directory = askdirectory(title="Select directory", mustexist=1)
            if directory:
                directory = str(directory)
                if os.path.isdir(directory):
                    if self.nbForm.get(): nb = self.nbForm.get()
                    else: nb = 0

                    r = reader.ReaderManager().waitForCard(5, "PcscReader", int(nb))
                    attack = macTraceability.MacTraceability(Iso7816(r))
                    if attack.setMRZ(self.mrzForm.get()):
                        attack.savePair(directory)
                        tkMessageBox.showinfo("Save successful", "The pair has bee saved in:\n{0}".format(directory))
                    else:
                        tkMessageBox.showerror("Error: Wrong MRZ", "The check digits are not correct")
                else:
                    tkMessageBox.showerror("Error: save", "The path you selected is not a directory")
        except Exception, msg:
            tkMessageBox.showerror("Error: save", str(msg))
    
    # CHECK FROM FILE
    def checkFromFile(self):
        try:
            
            directory = askopenfilename(title="Select file")
            if directory:
                directory = str(directory)
                if os.path.isfile(directory):
                    if self.nbForm.get(): nb = self.nbForm.get()
                    else: nb = 0
                    if self.coForm.get(): co = self.coForm.get()
                    else: co = 1.7
                    r = reader.ReaderManager().waitForCard(5, "PcscReader", int(nb))
                    attack = macTraceability.MacTraceability(Iso7816(r))
                    if self.frenchVar.get(): attack.reachMaxDelay()
                    self.writeToLog("Does the pair belongs the the passport scanned: {0}".format(attack.checkFromFile(directory, co)))
                else:
                    tkMessageBox.showerror("Error: save", "The path you selected is not a directory")
        except Exception, msg:
            tkMessageBox.showerror("Error: save", str(msg))
    
    # TEST
    def test(self):
        try:

            if self.nbForm.get(): nb = self.nbForm.get()
            else: nb = 0

            r = reader.ReaderManager().waitForCard(5, "PcscReader", int(nb))
            attack = macTraceability.MacTraceability(Iso7816(r))
            if attack.setMRZ(self.mrzForm.get()):
                if self.untilForm.get(): until = int(self.untilForm.get())
                else: until = 20
                if self.perDelayForm.get(): per_delay = int(self.perDelayForm.get())
                else: per_delay = 10
                
                j = 0
                while j<until:
                    self.writeToLog("Average: {0}".format(attack.test(j, per_delay)))
                    self.writeToLog("Delay increased between {0} and {1} error(s)".format(j, j+1))
                    j+=1
            else:
                tkMessageBox.showerror("Error: Wrong MRZ", "The check digits are not correct")

        except Exception, msg:
            tkMessageBox.showerror("Error: is vulnerable", str(msg))
        
    # BAC RESET
    def reset(self):
        try:
            if self.nbForm.get(): nb = self.nbForm.get()
            else: nb = 0

            r = reader.ReaderManager().waitForCard(5, "PcscReader", int(nb))
            attack = macTraceability.MacTraceability(Iso7816(r))
            if attack.setMRZ(self.mrzForm.get()):
                attack.rstBAC()
                self.writeToLog("BAC reset")
            else:
                tkMessageBox.showerror("Error: Wrong MRZ", "The check digits are not correct")
        except Exception, msg:
            tkMessageBox.showerror("Error: is vulnerable", str(msg))
    
    # DEMO
    def demo(self):
        try:
            if self.nbForm.get(): nb = self.nbForm.get()
            else: nb = 0

            r = reader.ReaderManager().waitForCard(5, "PcscReader", int(nb))
            attack = macTraceability.MacTraceability(Iso7816(r))
            if attack.setMRZ(self.mrzForm.get()):
                tkMessageBox.showinfo("Passport scanned", "Press ok then remove your passport from the reader.\nWait 5s before testing if a passport match.")
                if attack.demo():
                    self.writeToLog("This passport match the one scanned")
            else:
                tkMessageBox.showerror("Error: Wrong MRZ", "The check digits are not correct")
        except Exception, msg:
            tkMessageBox.showerror("Error: is vulnerable", str(msg))
    
    
    ################
    # HELP DIALOGS #
    ################
    
    def helpVulnDialog(self):
        title = "is vulnerable?"
        text = "Check whether a passport is vulnerable:\n\
    - Initiate a legitimate BAC and store a pair of message/MAC\n\
    - Reset a BAC with a random number for mutual authentication and store the answer together with the response time\n\
    - Reset a BAC and use the pair of message/MAC from step 1 and store the answer together with the response time\n\
\n\
If answers are different, this means the the passport is vulnerable.\n\
If not, the response time is compared. If the gap is wide enough, the passport might be vulnerable.\n\
\n\
Note: The French passport (and maybe others) implemented a security against brute forcing:\n\
anytime the BAC fail, an incremented delay occur before responsding.\n\
That's the reson why we need to establish a proper BAC to reset the delay to 0\n\
Note 2: The default cut off set to 1.7ms is based on the paper from Tom Chotia and Vitaliy Smirnov:\n\
A traceability Attack Against e-Pasport.\n\
They figured out a 1.7 cut-off suit for every country they assessed without raising low rate of false-positive and false-negative\n\
\n\
@param CO: The cut off used to determine whether the response time is long enough to considerate the passport as vulnerable\n\
@type CO: an integer that represent the cut off in milliseconds\n\
\n\
@return: A boolean where True means that the passport seems to be vulnerable and False means doesn't"
        InfoBoxWindows(self, title, text)
    
    def helpSaveDialog(self):
        title = "save pair"
        text = "savePair stores a message with its valid MAC in a file.\n\
The pair can be used later, in a futur attack, to define if the passport is the one that creates the pair (See checkFromFile()).\n\
If the path doesn't exist, the folders and sub-folders will be create.\n\
If the file exist, a number will be add automatically.\n\
\n\
@param path: The path where the file has to be create. It can be relative or absolute.\n\
@type path: A string (e.g. '/home/doe/' or 'foo/bar')\n\
@param filename: The name of the file where the pair will be saved\n\
@type filename: A string (e.g. 'belgian-pair' or 'pair.data')\n\
\n\
@return: the path and the name of the file where the pair has been saved."
        InfoBoxWindows(self, title, text)
    
    def helpCheckDialog(self):
        title = "check from file"
        text = "checkFromFile read a file that contains a pair and check if the pair has been capture from the passport .\n\
\n\
@param path: The path of the file where the pair has been saved.\n\
@type path: A string (e.g. '/home/doe/pair' or 'foo/bar/pair.data')\n\
@param CO: The cut off used to determine whether the response time is long enough to considerate the passport as vulnerable\n\
@type CO: an integer that represent the cut off in milliseconds\n\
\n\
@return: A boolean where True means that the passport is the one who create the pair in the file."
        InfoBoxWindows(self, title, text)
    
    def helpTestDialog(self):
        title = "test"
        text = "test is a method developped for analysing the response time of password whenever a wrong command is sent\n\
French passport has an anti MRZ brute forcing. This method help to highlight the behaviour\n\
Note: It might take a while before getting the results\n\
\n\
@param until: Number of wrong message to send before comparing the time delay\n\
@type until: An integer\n\
@param per_delay: how result per delay you want to output\n\
@type per_delay: An integer"
        InfoBoxWindows(self, title, text)
    
    def helpMaxDialog(self):
        title = "reach max"
        text = "Send a 13 (or more) wrong pair in order to reach the longest delay\n\
Note: Useful only for passport with anti MRZ brute forcing security."
        InfoBoxWindows(self, title, text)
    
    def helpRstDialog(self):
        title = "reset BAC"
        text = "Establish a legitimate BAC with the passport then reset the connection."
        InfoBoxWindows(self, title, text)
    
    def helpDemoDialog(self):
        title = "demo"
        text = "Here is a little demo to show how accurate is the traceability attack.\n\
Please note that the French passport will most likely output a false positive because of the anti brute forcing delay.\n\
\n\
@param CO: The cut off used to determine whether the response time is long enough to considerate the passport as vulnerable\n\
@type CO: an integer that represent the cut off in milliseconds\n\
@param valisate: check 3 time before validate the passport as identified\n\
@type validate: An integer that represent the number of validation\n\
\n\
@return: A boolean True whenever the initial passport is on the reader"
        InfoBoxWindows(self, title, text)
        
    def helpConfigDialog(self):
        title = "configuration"
        text = "Reader #: (optional) The number of the reader.\n\
For instance, the Omnikey 5321 use the reader number 1 for the RFID communication\n\
\n\
French passport: French passport implement an anti brute-force\n\
This means anytime a BAC fail, a delay increment before the passport responce.\n\
The MAC traceability is based on the reponse time. Therefore it is impotrant to\n\
reach the maximum delay. By selecting 'French passport', the application will run\n\
14 wrong BAC.\n\
Note: If 'French passport' is selected, you will reach a delay of about 15s per\n\
BAC query"
        InfoBoxWindows(self, title, text)
        

######
# HELP
######

class InfoBoxWindows(Toplevel):
    def __init__(self, master, title_dialog, text_dialog):
        Toplevel.__init__(self, master)
        self.title("Help: {0}".format(title_dialog))
        self.resizable(False,False)
        
        helpFrame = Frame(self, relief=RAISED, borderwidth=0)
        helpFrame.pack(fill=BOTH, expand=1)
        
        helpLabel = Label(helpFrame, text=text_dialog, justify=LEFT)
        helpLabel.pack(padx=5, pady=5)
        
        closeButton = Button(helpFrame, text="Close", command=self.destroy)
        closeButton.pack(padx=5, pady=5)

